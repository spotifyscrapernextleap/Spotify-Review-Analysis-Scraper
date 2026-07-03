"""Phase 4 — Layer-1 broad categorisation (Groq llama-3.1-8b-instant).

MULTI-LABEL: each review gets 1-3 categories (most are 1). Categories:
discovery, tech, ux, pricing, catalogue, audio, updates, other — plus the
exclusive routing labels `none` (contentless -> Tier C) and `podcast`
(podcast-only -> DISCARDED, out of scope). Also a sentiment + confidence.

- Android: classifies the stratified month SAMPLE.
- iOS: classifies ALL substantive candidates (census).
- Round-robins across all Groq keys (separate accounts) to multiply the daily
  token budget; daily-exhausted keys drop out; resumable by review id.

Run:
  python -m phases.phase-4-layer1-broad.classify <android|ios> [--limit N] [--batch 25] [--calibrate]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import deque
from datetime import datetime, timezone

from dotenv import load_dotenv

from common import config as C
from common.io import read_jsonl, write_json
from common.logging_setup import get_logger

log = get_logger("phase4.layer1")
load_dotenv(dotenv_path=str(C.ROOT / ".env"))

PROMPT_VERSION = "v5-multilabel-2026-06-25"
DISPLAY_CATS = set(C.CATEGORY_IDS)                 # discovery,tech,ux,pricing,catalogue,audio,updates,other
VALID = DISPLAY_CATS | {"none"}
VALID_SENT = {"positive", "negative", "mixed"}
TPM_LIMIT = 6000

# Podcast-only discard is deterministic (the 8B over-fires on any podcast mention).
# Discard ONLY if a podcast term is present AND none of a broad set of music/app/UX
# signals — so any review carrying a real app claim ("easy to use", "crashes",
# "ads") is kept. Bias is heavily toward KEEP; only near-pure podcast reviews drop.
_PODCAST_RE = re.compile(r"\bpodcast", re.I)
_KEEP_RE = re.compile(
    r"\b(music|song|playlist|artist|album|track|audio|shuffle|listen|tune|lyric|"
    r"radio|mix|app|use|using|easy|interface|navigat|search|setting|crash|bug|lag|"
    r"ad|ads|premium|price|subscri|account|login|update|sound|quality|play|skip|"
    r"offline|download|widget|screen)", re.I)


def is_podcast_only(text: str) -> bool:
    t = text or ""
    return bool(_PODCAST_RE.search(t)) and not _KEEP_RE.search(t)


def filter_podcast(records: list[dict]) -> tuple[list[dict], int]:
    kept = [r for r in records if not is_podcast_only(r.get("text") or "")]
    return kept, len(records) - len(kept)

SYSTEM = """You are a precise classifier for Spotify app-store reviews. For EACH numbered review return the category/categories it raises, a sentiment, and a confidence.

Assign 1 to 3 categories. MOST reviews are ONE category; use 2-3 ONLY when the review genuinely raises multiple distinct issues. Choose from:

- discovery: music discovery & recommendations — Discover Weekly / Release Radar / Daily Mix / "mixes", the recommendation algorithm, SMART SHUFFLE or autoplay choosing songs, shuffle not being random, repetition / "same songs again", taste matching, songs auto-added to your playlists.
- tech: technical reliability — crashes, freezing, bugs, lag, songs stopping/skipping, playback failing, offline/download problems, connectivity, casting (Sonos / smart speakers), account-creation or "something went wrong" errors.
- ux: interface, navigation, layout, design, search usability, settings, playlist organisation, widgets, lockscreen controls, control/feature requests.
- pricing: price, subscription, billing, family plan, login/account access — and ALWAYS any complaint about ADS / advertisements / "too many ads" / ad length. ADS ALWAYS GO HERE, never tech or catalogue.
- catalogue: AVAILABILITY only — a specific song/album/artist is MISSING, greyed-out, or not in the library; regional restrictions; missing lyrics. NOT for the wrong song playing (that is discovery or tech), NOT for playlist curation quality (that is discovery).
- audio: sound/audio QUALITY only — bitrate, clarity, "quality fades in/out", equalizer, volume.
- updates: the review is about a recent APP UPDATE / new version ("the new update", "since the last update"). `updates` is ADDITIVE — ALWAYS also include the affected category in the same list (e.g. ["updates","tech"]; "love the new mix update" -> ["discovery","updates"]). Use ["updates"] alone ONLY if the review says nothing but "they changed it".
- other: a clear, specific product claim that fits none of the above.

IMPORTANT: if a review praises one aspect but complains about another, classify by the COMPLAINT and ignore the praise (e.g. "great audio but I can't pick songs without premium" -> pricing, NOT audio).

EXCLUSIVE label — use ALONE, never combined with others:
- none: NO specific claim — pure praise, insult, or noise ("best app ever", "love it", "trash", "way better than YouTube", vague emoji). Use 'none' for vague positivity, NOT 'other'.

sentiment: positive | negative | mixed
confidence: high | low (low when ambiguous)

Return ONLY JSON: {"results":[{"i":1,"categories":["discovery"],"sentiment":"negative","confidence":"high"}, ...]} — exactly one object per input review, preserving numbering; "categories" is a list of 1-3 ids (or ["none"])."""


class StopExhausted(Exception):
    pass


class TPMPacer:
    def __init__(self, limit): self.limit = limit; self.events = deque()
    def wait(self, need):
        while True:
            now = time.time()
            while self.events and now - self.events[0][0] > 60:
                self.events.popleft()
            if sum(t for _, t in self.events) + need <= self.limit * 0.95 or not self.events:
                return
            time.sleep(max(60 - (now - self.events[0][0]) + 0.2, 0.5))
    def record(self, tok): self.events.append((time.time(), tok))


class KeyPool:
    def __init__(self, keys):
        from groq import Groq
        self.clients = [Groq(api_key=k) for k in keys]
        self.pacers = [TPMPacer(TPM_LIMIT) for _ in keys]
        self.tokens = [0] * len(keys)
        self.healthy = list(range(len(keys)))
        self._rr = 0

    def _next(self):
        if not self.healthy:
            raise StopExhausted()
        idx = self.healthy[self._rr % len(self.healthy)]
        self._rr += 1
        return idx

    def complete(self, messages, est):
        from groq import RateLimitError
        attempts = 0
        while True:
            attempts += 1
            idx = self._next()
            self.pacers[idx].wait(est)
            try:
                r = self.clients[idx].chat.completions.create(
                    model=C.GROQ_MODEL_BROAD, messages=messages, temperature=0,
                    response_format={"type": "json_object"}, max_tokens=4000)
                used = r.usage.prompt_tokens + r.usage.completion_tokens
                self.pacers[idx].record(used)
                self.tokens[idx] += used
                return r, r.usage.prompt_tokens, r.usage.completion_tokens
            except RateLimitError as e:
                if any(s in str(e).lower() for s in ("per day", "tpd", "rpd", "per_day")):
                    log.warning("  key#%d DAILY-exhausted -> dropping", idx + 1)
                    if idx in self.healthy:
                        self.healthy.remove(idx)
                    continue
                time.sleep(3)
                if attempts > 6 * max(len(self.healthy), 1):
                    raise
            except Exception as e:  # noqa: BLE001
                log.warning("  key#%d error: %s", idx + 1, e)
                time.sleep(2)
                if attempts > 8:
                    return None, 0, 0


def _messages(batch):
    lines = [f"{i+1}. {(r.get('text') or '').strip()}" for i, r in enumerate(batch)]
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Reviews:\n" + "\n".join(lines)}]


def _parse(content, n):
    try:
        obj = json.loads(content)
        res = obj.get("results", obj if isinstance(obj, list) else [])
        return res if isinstance(res, list) and len(res) == n else None
    except Exception:  # noqa: BLE001
        return None


def _clean_cats(raw):
    """Normalise model's category list to 1-3 valid ids; exclusive none/podcast."""
    if isinstance(raw, str):
        raw = [raw]
    cats = [c for c in (raw or []) if c in VALID]
    if not cats:
        return ["none"]
    if "none" in cats:
        return ["none"] if len(cats) == 1 else [c for c in cats if c != "none"][:3]
    return cats[:3]


def classify_records(pool: "KeyPool", records: list[dict], batch_size: int):
    """Yield (record, categories, sentiment, confidence, pt, ct, failed) per record.

    FAIL-CLOSED: a batch that will not parse after 3 tries is retried ONE REVIEW AT A
    TIME (single-item JSON is far more robust than a big batch that truncates mid-array).
    A review that STILL will not parse is abstained to ['none'] with failed=True — an
    auditable marker, never a guessed label. 'none' routes it out of every category, so a
    failure can never inflate a count. Reused by the full run and the prompt validator."""
    for s in range(0, len(records), batch_size):
        batch = records[s:s + batch_size]
        est = sum(len(r.get("text") or "") for r in batch) // 3 + 400
        parsed = None; pt = ct = 0
        for _try in range(3):  # retry on item-count mismatch before falling back (matters at large batch)
            resp, pt, ct = pool.complete(_messages(batch), est)
            parsed = _parse(resp.choices[0].message.content, len(batch)) if resp else None
            if parsed is not None:
                break
            log.warning("  batch parse/length mismatch (n=%d, try %d)", len(batch), _try + 1)
        failed_flags = [False] * len(batch)
        if parsed is None:
            log.warning("  batch of %d failed 3x — retrying per-review (fail-closed)", len(batch))
            parsed = []
            for i, one in enumerate(batch):
                one_parsed = None
                for _t in range(2):
                    resp1, p1, c1 = pool.complete(_messages([one]), len(one.get("text") or "") // 3 + 200)
                    one_parsed = _parse(resp1.choices[0].message.content, 1) if resp1 else None
                    if one_parsed:
                        pt += p1; ct += c1
                        break
                if one_parsed:
                    parsed.append(one_parsed[0])
                else:
                    log.error("  REVIEW %s uncodeable after per-review retry — 'none'+failed (fail-closed)",
                              one.get("review_id"))
                    parsed.append({"categories": ["none"], "sentiment": "mixed", "confidence": "low"})
                    failed_flags[i] = True
        for rec, lab, failed in zip(batch, parsed, failed_flags):
            cats = _clean_cats(lab.get("categories", lab.get("category")))
            sent = lab.get("sentiment") if lab.get("sentiment") in VALID_SENT else "mixed"
            conf = "high" if lab.get("confidence") == "high" else "low"
            yield rec, cats, sent, conf, pt, ct, failed


def _src(track):
    return (C.INTERIM_DIR / "android_layer1_sample.jsonl") if track == "android" \
        else (C.INTERIM_DIR / "ios" / "substantive_candidates.jsonl")


def _write_status(track, total, done, pool, stopped, complete):
    write_json(C.INTERIM_DIR / f"{track}_layer1_status.json", {
        "track": track, "prompt_version": PROMPT_VERSION, "total": total, "done": done,
        "remaining": total - done, "complete": complete, "stopped_exhausted": stopped,
        "tokens_per_key": pool.tokens if pool else None,
        "healthy_keys": len(pool.healthy) if pool else None,
        "updated": datetime.now(timezone.utc).isoformat()})


def run(track, limit, batch_size, calibrate):
    keys = C.groq_api_keys()
    if not keys:
        raise SystemExit("No GROQ_API_KEY* in .env")
    out_path = C.INTERIM_DIR / f"{track}_layer1.jsonl"
    lock = C.INTERIM_DIR / f"{track}_layer1.lock"
    if not calibrate and lock.exists():
        raise SystemExit(f"Lock present ({lock}); another run may be active.")
    if not calibrate:
        lock.write_text(f"pid={os.getpid()} {datetime.now(timezone.utc).isoformat()}")
    pool = KeyPool(keys)
    log.info("[%s] %d key(s); prompt=%s", track, len(keys), PROMPT_VERSION)

    rows = list(read_jsonl(_src(track)))
    if limit:
        rows = rows[:limit]
    rows, n_pod = filter_podcast(rows)        # deterministic podcast-only discard (out of scope)
    log.info("[%s] discarded %d podcast-only reviews", track, n_pod)
    done_ids = {r["review_id"] for r in read_jsonl(out_path)} if (out_path.exists() and not calibrate) else set()
    todo = [r for r in rows if r["review_id"] not in done_ids]
    log.info("[%s] %d to classify (%d done), batch=%d", track, len(todo), len(done_ids), batch_size)

    t0 = time.time(); n = 0; n_failed = 0; cats_count = {}; fh = None if calibrate else open(out_path, "a", encoding="utf-8")
    stopped = False
    try:
        gen = classify_records(pool, todo, batch_size)
        while True:
            try:
                rec, cats, sent, conf, pt, ct, failed = next(gen)
            except StopExhausted:
                log.warning("[%s] ALL KEYS exhausted — stopping; resume later", track); stopped = True; break
            except StopIteration:
                break
            out = {"review_id": rec["review_id"], "store": rec["store"], "country": rec.get("country"),
                   "rating": rec.get("rating"), "date": rec.get("date"), "text": rec.get("text"),
                   "categories": cats, "sentiment": sent, "confidence": conf}
            if failed:
                out["coding_failed"] = True          # auditable: routed to 'none', never a guessed label
                n_failed += 1
            for c in cats:
                cats_count[c] = cats_count.get(c, 0) + 1
            n += 1
            if not calibrate:
                fh.write(json.dumps(out, ensure_ascii=False) + "\n"); fh.flush()
            if n % 500 == 0:
                log.info("  [%s] %d/%d, tokens=%d, keys=%d", track, n, len(todo), sum(pool.tokens), len(pool.healthy))
                if not calibrate:
                    _write_status(track, len(rows), len(done_ids) + n, pool, False, False)
    finally:
        if fh: fh.close()
        if not calibrate:
            td = len(done_ids) + n
            _write_status(track, len(rows), td, pool, stopped, td >= len(rows) and not stopped)
            lock.unlink(missing_ok=True)
    tot = sum(pool.tokens)
    log.info("[%s] %s n=%d tokens=%d (%.1f/rev) %.0fs per-key=%s", track,
             "STOPPED" if stopped else "DONE", n, tot, tot / n if n else 0, time.time() - t0, pool.tokens)
    if n_failed:
        log.error("[%s] %d review(s) uncodeable after per-review retry — routed to 'none'+coding_failed "
                  "(fail-closed, auditable)", track, n_failed)
    log.info("  category occurrences: %s", dict(sorted(cats_count.items(), key=lambda x: -x[1])))
    return {"classified": n, "stopped": stopped, "cats": cats_count, "tokens": tot, "coding_failed": n_failed}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("track", choices=["android", "ios"])
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--batch", type=int, default=25)
    p.add_argument("--calibrate", action="store_true")
    a = p.parse_args()
    run(a.track, a.limit, a.batch, a.calibrate)
