"""Phase 5 — Layer-2 deep Discovery coding: OPEN-CODING pass (gpt-oss-120b).

Step 1 of Phase 5. Themes surface FREELY here — no fixed codebook yet. For each
discovery review the deep model emits 1-2 short free-form codes (2-4 word labels)
plus a VERBATIM snippet that justifies each. We then aggregate code frequencies
into a candidate codebook for the human-consolidation checkpoint (step 2).

This uses GROQ_MODEL_DEEP (separate rate-limit pool from the 8B Layer-1 model).

Run:
  python -m phases.phase-5-layer2-discovery.open_code [--limit N] [--batch 10]
Outputs:
  data/interim/phase5_opencode_raw.jsonl   — per-review codes + snippets
  data/interim/phase5_opencode_codes.json  — aggregated candidate code frequencies
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, deque

from dotenv import load_dotenv

from common import config as C
from common.io import read_jsonl, write_json
from common.logging_setup import get_logger

sys.stdout.reconfigure(encoding="utf-8")
log = get_logger("phase5.opencode")
load_dotenv(dotenv_path=str(C.ROOT / ".env"))

TPM_LIMIT = 6000  # conservative per-minute pacing per key

SYSTEM = """You are a qualitative researcher OPEN-CODING Spotify reviews. Every review below was already flagged as DISCOVERY-RELATED — your job is to find and name the discovery / recommendation / personalisation angle in each. There is NO fixed codebook — surface what is actually there.

"Discovery-related" is BROAD. Code anything touching: music discovery & recommendations (Discover Weekly, Release Radar, Daily Mix, "mixes", Wrapped, radio); the recommendation algorithm & taste-matching; smart shuffle / autoplay / AI DJ choosing what plays next; shuffle not being random; repetition / "same songs again"; recommendations too safe or stuck in a bubble; finding new music or finding specific music ("can find anything"); wanting more control over what's recommended; songs auto-added to playlists.

For EACH numbered review emit 1-2 short CODES, each 2-4 words, lowercase, naming the precise issue OR praise (e.g. "same songs repeat", "shuffle not random", "recs too safe", "filter bubble", "great discover weekly", "wants rec control", "autoplay bad picks", "comfort replay", "ai dj cuts songs", "wrapped loved", "finds anything"). Be specific and CONSISTENT — reuse identical wording for the same idea across reviews so codes aggregate.

For each code give a VERBATIM snippet: an exact substring copied from the review (no paraphrasing) that justifies it.

Code liberally — prefer naming a discovery angle over abstaining. Only if a review genuinely has ZERO discovery/recommendation/personalisation/finding content (a mis-flag — e.g. purely about ads, price, or a crash) return an empty codes list []. If it mentions discovery only vaguely, use "vague discovery complaint" or "vague discovery praise".

Return ONLY JSON: {"results":[{"i":1,"codes":[{"code":"same songs repeat","snippet":"it keeps playing the same 20 songs"}]}, ...]} — exactly one object per input review, preserving numbering."""


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
    """Round-robins the deep model across separate-account keys (own quota pool)."""
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
                    model=C.GROQ_MODEL_DEEP, messages=messages, temperature=0,
                    response_format={"type": "json_object"},
                    reasoning_effort="low", max_tokens=6000)
                used = r.usage.prompt_tokens + r.usage.completion_tokens
                self.pacers[idx].record(used)
                self.tokens[idx] += used
                return r
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
                log.warning("  key#%d error: %s", idx + 1, str(e)[:120])
                time.sleep(2)
                if attempts > 8:
                    return None


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


def run(limit, batch_size):
    keys = C.groq_api_keys()
    if not keys:
        raise SystemExit("No GROQ_API_KEY* in .env")
    rows = list(read_jsonl(C.INTERIM_DIR / "phase5_opencode_sample.jsonl"))
    if limit:
        rows = rows[:limit]
    pool = KeyPool(keys)
    log.info("open-coding %d reviews on %s, %d key(s), batch=%d",
             len(rows), C.GROQ_MODEL_DEEP, len(keys), batch_size)

    out_path = C.INTERIM_DIR / "phase5_opencode_raw.jsonl"
    code_counts: Counter = Counter()
    t0 = time.time(); n = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for s in range(0, len(rows), batch_size):
            batch = rows[s:s + batch_size]
            est = sum(len(r.get("text") or "") for r in batch) // 3 + 800
            parsed = None
            for _try in range(3):
                resp = pool.complete(_messages(batch), est)
                parsed = _parse(resp.choices[0].message.content, len(batch)) if resp else None
                if parsed is not None:
                    break
                log.warning("  batch parse/length mismatch (n=%d, try %d)", len(batch), _try + 1)
            if parsed is None:
                log.warning("  abstaining batch of %d", len(batch))
                parsed = [{"codes": []}] * len(batch)
            for rec, lab in zip(batch, parsed):
                codes = lab.get("codes") or []
                rec_codes = []
                for c in codes:
                    if isinstance(c, dict) and c.get("code"):
                        code = str(c["code"]).strip().lower()
                        rec_codes.append({"code": code, "snippet": (c.get("snippet") or "").strip()})
                        code_counts[code] += 1
                fh.write(json.dumps({"review_id": rec["review_id"], "rating": rec.get("rating"),
                                     "sentiment": rec.get("sentiment"), "text": rec.get("text"),
                                     "codes": rec_codes}, ensure_ascii=False) + "\n")
                n += 1
            log.info("  %d/%d coded, tokens=%d, keys=%d", n, len(rows), sum(pool.tokens), len(pool.healthy))

    write_json(C.INTERIM_DIR / "phase5_opencode_codes.json",
               {"model": C.GROQ_MODEL_DEEP, "n_reviews": n, "n_unique_codes": len(code_counts),
                "tokens": sum(pool.tokens),
                "codes": [{"code": c, "count": k} for c, k in code_counts.most_common()]})
    log.info("DONE n=%d unique_codes=%d tokens=%d %.0fs",
             n, len(code_counts), sum(pool.tokens), time.time() - t0)
    print("\nTOP CODES:")
    for c, k in code_counts.most_common(40):
        print(f"  {k:3d}  {c}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--batch", type=int, default=10)
    a = p.parse_args()
    run(a.limit, a.batch)
