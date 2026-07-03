"""Phase 4 validation — DISCOVERY RECALL PROBE (gpt-oss-120b).

Measures the 8B Layer-1 FALSE-NEGATIVE rate for `discovery`: how many real
discovery reviews did the 8B miss and file under pricing/tech/ux/etc.?

Method (mirror image of the Phase-5 open-coding pass): take a proportional random
sample of the CODEABLE NON-discovery pile, and ask the deep 120B model — using the
SAME discovery definition the 8B was given — whether each is actually a discovery
review. The hit rate is the estimated false-negative rate; reweighted onto the pile
it estimates how many discovery reviews are missing from the discovery count.

Run:
  python -m phases.phase-4-layer1-broad.recall_probe [--n 250] [--batch 10]
Outputs:
  data/interim/phase4_recall_probe.jsonl   — per-review verdicts + snippets
  data/interim/phase4_recall_probe.json    — summary (FN rate, per-pile, projection)
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, deque

from dotenv import load_dotenv

from common import config as C
from common.io import read_jsonl, write_json
from common.logging_setup import get_logger

sys.stdout.reconfigure(encoding="utf-8")
log = get_logger("phase4.recall")
load_dotenv(dotenv_path=str(C.ROOT / ".env"))

TPM_LIMIT = 6000

# SAME discovery definition the 8B Layer-1 prompt used, so the comparison is fair.
SYSTEM = """You are auditing Spotify app-store reviews for one specific topic: MUSIC DISCOVERY & RECOMMENDATIONS.

A review counts as DISCOVERY if it raises any of: Discover Weekly / Release Radar / Daily Mix / "mixes"; the recommendation algorithm or taste-matching; SMART SHUFFLE or autoplay / AI DJ choosing what plays; shuffle not being random; repetition / "same songs again"; recommendations being too safe / stuck / a filter bubble; finding new music or wanting to find specific music; wanting more control over what is recommended; songs auto-added to playlists; Wrapped as a discovery/taste feature.

It does NOT count as discovery if it is only about: ads / price / subscription; crashes / bugs / playback failing; login/account; sound quality; a specific song/artist simply being MISSING from the catalogue; pure UI layout with no discovery angle; generic praise/insult.

For EACH numbered review decide: is it ACTUALLY a discovery review? Be strict — only YES if there is genuine discovery content, not a passing word. If YES, give a VERBATIM snippet (exact substring) that shows it.

Return ONLY JSON: {"results":[{"i":1,"discovery":true,"snippet":"the recommendations are always the same songs"},{"i":2,"discovery":false,"snippet":""}, ...]} — exactly one object per input review, preserving numbering."""


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
    def __init__(self, keys, model=None):
        from groq import Groq
        self.clients = [Groq(api_key=k) for k in keys]
        self.pacers = [TPMPacer(TPM_LIMIT) for _ in keys]
        self.tokens = [0] * len(keys)
        self.healthy = list(range(len(keys)))
        self._rr = 0
        self.model = model or C.GROQ_MODEL_DEEP

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
                    model=self.model, messages=messages, temperature=0,
                    response_format={"type": "json_object"},
                    reasoning_effort="low", max_tokens=5000)
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


def build_sample(n):
    rows = list(read_jsonl(C.INTERIM_DIR / "android_layer1.jsonl"))
    pool = [r for r in rows
            if "discovery" not in (r.get("categories") or [])
            and (r.get("categories") or []) != ["none"]
            and len(r.get("text") or "") >= 40]
    random.seed(42)
    random.shuffle(pool)
    return pool[:n]


def run(n, batch_size):
    keys = C.groq_api_keys()
    if not keys:
        raise SystemExit("No GROQ_API_KEY* in .env")
    sample = build_sample(n)
    pool = KeyPool(keys)
    log.info("recall probe: %d non-discovery reviews on %s, %d key(s)",
             len(sample), C.GROQ_MODEL_DEEP, len(keys))

    out_path = C.INTERIM_DIR / "phase4_recall_probe.jsonl"
    missed_by_pile: Counter = Counter()
    total_by_pile: Counter = Counter()
    hits = []
    t0 = time.time(); n_done = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for s in range(0, len(sample), batch_size):
            batch = sample[s:s + batch_size]
            est = sum(len(r.get("text") or "") for r in batch) // 3 + 600
            parsed = None
            for _try in range(3):
                resp = pool.complete(_messages(batch), est)
                parsed = _parse(resp.choices[0].message.content, len(batch)) if resp else None
                if parsed is not None:
                    break
                log.warning("  batch mismatch (n=%d, try %d)", len(batch), _try + 1)
            if parsed is None:
                parsed = [{"discovery": False, "snippet": ""}] * len(batch)
            for rec, lab in zip(batch, parsed):
                is_disc = bool(lab.get("discovery"))
                cats = [c for c in (rec.get("categories") or []) if c != "none"]
                primary = cats[0] if cats else "?"
                total_by_pile[primary] += 1
                if is_disc:
                    missed_by_pile[primary] += 1
                    hits.append({"review_id": rec["review_id"], "orig_cats": rec.get("categories"),
                                 "rating": rec.get("rating"), "snippet": lab.get("snippet", ""),
                                 "text": rec.get("text")})
                fh.write(json.dumps({"review_id": rec["review_id"], "orig_cats": rec.get("categories"),
                                     "is_actually_discovery": is_disc, "snippet": lab.get("snippet", ""),
                                     "text": rec.get("text")}, ensure_ascii=False) + "\n")
                n_done += 1
            log.info("  %d/%d probed, missed=%d, tokens=%d", n_done, len(sample), len(hits), sum(pool.tokens))

    fn = len(hits) / n_done if n_done else 0
    # Wilson-ish 95% CI half-width for a proportion
    import math
    se = math.sqrt(fn * (1 - fn) / n_done) if n_done else 0
    ci = 1.96 * se
    # project onto the codeable non-discovery pile
    pile_size = len(build_sample(10**9))  # whole pool
    est_missed = round(fn * pile_size)
    summary = {
        "model": C.GROQ_MODEL_DEEP, "probed": n_done, "missed_discovery": len(hits),
        "false_negative_rate": round(fn, 4), "ci95_halfwidth": round(ci, 4),
        "nondisc_codeable_pile": pile_size, "est_discovery_missed_in_pile": est_missed,
        "missed_by_pile": dict(missed_by_pile), "total_by_pile": dict(total_by_pile),
        "tokens": sum(pool.tokens),
    }
    write_json(C.INTERIM_DIR / "phase4_recall_probe.json", summary)
    log.info("DONE %.0fs tokens=%d", time.time() - t0, sum(pool.tokens))
    print("\n========== DISCOVERY RECALL PROBE ==========")
    print(f"probed (non-discovery pile): {n_done}")
    print(f"actually discovery (8B MISSED): {len(hits)}  ->  FN rate = {fn*100:.1f}%  (95% CI +/-{ci*100:.1f}%)")
    print(f"per-pile miss rate:")
    for p in sorted(total_by_pile, key=lambda x: -total_by_pile[x]):
        m, t = missed_by_pile.get(p, 0), total_by_pile[p]
        print(f"   {p:10s} {m:3d}/{t:3d}  ({100*m/t:.0f}%)")
    print(f"\nProjected onto the {pile_size} codeable non-discovery reviews:")
    print(f"   ~{est_missed} real discovery reviews missed by 8B")
    print(f"   current discovery count = 2359 (codeable). corrected ~= {2359+est_missed} before FP removal")
    print("\nSample of MISSED discovery reviews:")
    for h in hits[:8]:
        print(f"   [{h['orig_cats']}] snippet={h['snippet'][:90]!r}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=250)
    p.add_argument("--batch", type=int, default=10)
    a = p.parse_args()
    run(a.n, a.batch)
