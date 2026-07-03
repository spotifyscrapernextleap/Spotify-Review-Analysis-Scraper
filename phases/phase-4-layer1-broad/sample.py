"""Phase 4 prep — stratified month sample for Android Layer-1 classification.

Android is census-scraped but LLM-classified on a SAMPLE (free-tier budget).
iOS is NOT sampled (it is classified in full — census).

Allocation rule (user-specified): per-month sample size scales between a
2,000 FLOOR and a 4,000 CAP, linearly with that month's substantive volume.
- High-volume months (e.g. a feature-update spike) earn up to 4k — not
  under-sampled relative to their true size.
- Low-volume months keep the 2k floor — well-estimated, not drowned.
So each month is sized on its own; they don't compete over one fixed budget.

Selection: simple random sample within each month, fixed seed (reproducible),
drawn from the FULL month population (census) — so it is a true random sample,
not a recency-biased slice.

Output:
  data/interim/android_layer1_sample.jsonl   (reviews to classify)
  data/interim/android_sample_allocation.json (per-month n + report)
"""
from __future__ import annotations

import random
from collections import defaultdict

from common import config as C
from common.io import read_jsonl, write_json, write_jsonl
from common.logging_setup import get_logger

log = get_logger("phase4.sample")

FLOOR = 2000
CAP = 4000
SEED = 42


def run() -> dict:
    cand = list(read_jsonl(C.INTERIM_DIR / "android" / "substantive_candidates.jsonl"))
    by_month: dict[str, list] = defaultdict(list)
    for r in cand:
        by_month[(r.get("date") or "unknown")[:7]].append(r)
    months = sorted(m for m in by_month if m != "unknown")
    vols = {m: len(by_month[m]) for m in months}
    vmin, vmax = min(vols.values()), max(vols.values())

    rng = random.Random(SEED)
    sample, alloc = [], []
    for m in months:
        avail = vols[m]
        if vmax == vmin:
            target = FLOOR
        else:
            frac = (avail - vmin) / (vmax - vmin)
            target = round(FLOOR + frac * (CAP - FLOOR))
        n = min(target, avail)
        picked = rng.sample(by_month[m], n)
        for r in picked:
            r["_month"] = m
        sample.extend(picked)
        alloc.append({"month": m, "available": avail, "target": target, "sampled": n})

    write_jsonl(C.INTERIM_DIR / "android_layer1_sample.jsonl", sample)
    report = {"floor": FLOOR, "cap": CAP, "seed": SEED,
              "total_candidates": len(cand), "total_sampled": len(sample),
              "allocation": alloc}
    write_json(C.INTERIM_DIR / "android_sample_allocation.json", report)

    log.info("sampled %d of %d candidates across %d months", len(sample), len(cand), len(months))
    for a in alloc:
        log.info("  %s: available=%-6d -> sampled=%d", a["month"], a["available"], a["sampled"])
    return report


if __name__ == "__main__":
    run()
