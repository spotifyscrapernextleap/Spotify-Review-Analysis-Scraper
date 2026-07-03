"""Phase 4 -> Phase 5 bridge — DISCOVERY RECALL RECOVERY (gpt-oss-120b).

The recall probe found the 8B's missed discovery reviews hide almost entirely in
the `ux` (18%) and `updates` (14%) piles; pricing/tech/etc. are clean (<=2%). So we
run the 120B discovery-detector over the FULL ux + updates piles (a census, not a
sample) to (a) get reliable per-pile miss rates and (b) RECOVER the missed discovery
reviews and fold them into the Phase 5 deep-coding pool.

Resumable: skips review_ids already in the verdicts file.

Run:
  python -m phases.phase-4-layer1-broad.recover_discovery [--piles ux,updates] [--batch 10]
Outputs:
  data/interim/phase4_recover_verdicts.jsonl  — every probed review + verdict (resume log)
  data/interim/android_discovery_recovered.jsonl — the recovered discovery reviews
  data/interim/android_discovery_pool.jsonl   — FINAL Phase-5 pool (orig 2,359 + recovered, deduped)
  data/interim/phase4_recover_summary.json    — per-pile census miss rates
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter

from dotenv import load_dotenv

from common import config as C
from common.io import read_jsonl, write_json
from common.logging_setup import get_logger

sys.stdout.reconfigure(encoding="utf-8")
log = get_logger("phase4.recover")
load_dotenv(dotenv_path=str(C.ROOT / ".env"))

# Reuse the probe's detector (same discovery definition the 8B was given).
_spec = importlib.util.spec_from_file_location(
    "recall_probe", str(C.PHASES_DIR / "phase-4-layer1-broad" / "recall_probe.py"))
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)


def build_pool(piles):
    rows = list(read_jsonl(C.INTERIM_DIR / "android_layer1.jsonl"))
    out = []
    for r in rows:
        cats = r.get("categories") or []
        if "discovery" in cats or cats == ["none"]:
            continue
        if len(r.get("text") or "") < 40:
            continue
        if any(p in cats for p in piles):
            out.append(r)
    return out


def run(piles, batch_size):
    keys = C.groq_api_keys()
    if not keys:
        raise SystemExit("No GROQ_API_KEY* in .env")
    pool_reviews = build_pool(piles)
    verdicts_path = C.INTERIM_DIR / "phase4_recover_verdicts.jsonl"
    done = {r["review_id"] for r in read_jsonl(verdicts_path)} if verdicts_path.exists() else set()
    todo = [r for r in pool_reviews if r["review_id"] not in done]
    log.info("recovery over piles=%s: %d reviews (%d done), batch=%d",
             piles, len(todo), len(done), batch_size)

    pool = rp.KeyPool(keys)
    t0 = time.time(); n = 0; recovered = 0
    vf = open(verdicts_path, "a", encoding="utf-8")
    try:
        for s in range(0, len(todo), batch_size):
            batch = todo[s:s + batch_size]
            est = sum(len(r.get("text") or "") for r in batch) // 3 + 600
            parsed = None
            for _try in range(3):
                resp = pool.complete(rp._messages(batch), est)
                parsed = rp._parse(resp.choices[0].message.content, len(batch)) if resp else None
                if parsed is not None:
                    break
            if parsed is None:
                parsed = [{"discovery": False, "snippet": ""}] * len(batch)
            for rec, lab in zip(batch, parsed):
                is_disc = bool(lab.get("discovery"))
                vf.write(json.dumps({"review_id": rec["review_id"], "orig_cats": rec.get("categories"),
                                     "is_discovery": is_disc, "snippet": lab.get("snippet", ""),
                                     "rating": rec.get("rating"), "store": rec.get("store"),
                                     "country": rec.get("country"), "date": rec.get("date"),
                                     "sentiment": rec.get("sentiment"), "text": rec.get("text")},
                                    ensure_ascii=False) + "\n")
                vf.flush()
                n += 1
                if is_disc:
                    recovered += 1
            if (s // batch_size) % 10 == 0:
                log.info("  %d/%d probed, recovered=%d, tokens=%d, keys=%d",
                         n, len(todo), recovered, sum(pool.tokens), len(pool.healthy))
    finally:
        vf.close()

    # Build outputs from the full verdicts log (idempotent)
    all_v = list(read_jsonl(verdicts_path))
    hits = [v for v in all_v if v.get("is_discovery")]
    # per-pile census miss rate
    miss, tot = Counter(), Counter()
    for v in all_v:
        cats = [c for c in (v.get("orig_cats") or []) if c != "none"]
        for p in piles:
            if p in cats:
                tot[p] += 1
                if v.get("is_discovery"):
                    miss[p] += 1
    # recovered discovery reviews -> layer1-shaped records, marked recovered
    rec_path = C.INTERIM_DIR / "android_discovery_recovered.jsonl"
    with open(rec_path, "w", encoding="utf-8") as fh:
        for v in hits:
            fh.write(json.dumps({"review_id": v["review_id"], "store": v.get("store"),
                                 "country": v.get("country"), "rating": v.get("rating"),
                                 "date": v.get("date"), "text": v.get("text"),
                                 "sentiment": v.get("sentiment"), "recovered_from": v.get("orig_cats"),
                                 "recover_snippet": v.get("snippet")}, ensure_ascii=False) + "\n")
    # FINAL Phase-5 pool: original discovery + recovered, deduped by id
    orig = [r for r in read_jsonl(C.INTERIM_DIR / "android_layer1.jsonl")
            if "discovery" in (r.get("categories") or [])]
    pool_path = C.INTERIM_DIR / "android_discovery_pool.jsonl"
    seen = set(); n_pool = 0
    with open(pool_path, "w", encoding="utf-8") as fh:
        for r in orig:
            seen.add(r["review_id"])
            fh.write(json.dumps({**r, "discovery_source": "layer1"}, ensure_ascii=False) + "\n"); n_pool += 1
        for v in hits:
            if v["review_id"] in seen:
                continue
            seen.add(v["review_id"])
            fh.write(json.dumps({"review_id": v["review_id"], "store": v.get("store"),
                                 "country": v.get("country"), "rating": v.get("rating"),
                                 "date": v.get("date"), "text": v.get("text"),
                                 "sentiment": v.get("sentiment"),
                                 "discovery_source": "recovered"}, ensure_ascii=False) + "\n"); n_pool += 1

    summary = {"piles": piles, "probed": len(all_v), "recovered": len(hits),
               "per_pile": {p: {"missed": miss.get(p, 0), "total": tot.get(p, 0),
                                "rate": round(miss.get(p, 0) / tot[p], 4) if tot.get(p) else None}
                            for p in piles},
               "orig_pool": len(orig), "final_pool": n_pool, "tokens": sum(pool.tokens)}
    write_json(C.INTERIM_DIR / "phase4_recover_summary.json", summary)
    log.info("DONE %.0fs tokens=%d", time.time() - t0, sum(pool.tokens))
    print("\n========== DISCOVERY RECOVERY (census of ux+updates) ==========")
    for p in piles:
        t, m = tot.get(p, 0), miss.get(p, 0)
        print(f"  {p:10s}: {m}/{t} are actually discovery  ({100*m/t:.0f}%)" if t else f"  {p}: 0")
    print(f"\n  recovered discovery reviews : {len(hits)}")
    print(f"  Phase-5 pool: {len(orig)} (layer1) + {n_pool-len(orig)} (recovered) = {n_pool}")
    print("\n  sample recovered snippets:")
    for v in hits[:10]:
        print(f"    [{v.get('orig_cats')}] {(v.get('snippet') or '')[:85]!r}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--piles", default="ux,updates")
    p.add_argument("--batch", type=int, default=10)
    a = p.parse_args()
    run([x.strip() for x in a.piles.split(",") if x.strip()], a.batch)
