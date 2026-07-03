"""Phase 6 (primary) — build the DISCOVERY SUB-THEME gold set.

Validates Layer-2: do the codebook sub-themes actually fit the discovery reviews?
Samples 50 of the 1,792 deep-coded discovery reviews, stratified across the 11
codebook themes (+ emerging), weighted toward MULTI-theme / boundary cases (incl.
the contentious freegate/control free-tier edge). The user labels each review with
the codebook sub-theme(s) it really raises — and can flag reviews the codebook MISSES
(surfacing gaps). Model predictions stay in a hidden key so labeling is blind.

Run:
  python -m phases.phase-6-gold-validation.build_subtheme_gold_set
"""
from __future__ import annotations

import csv
import random

from common import config as C
from common.io import read_jsonl, write_json

random.seed(42)

NAMES = {
    "repeat": "Same songs on repeat", "shuffle": "Shuffle isn't random",
    "autoplay": "Autoplay forces songs", "safe": "Recs too safe / filter bubble",
    "mismatch": "Irrelevant / wrong recs", "pushy": "Unwanted recs pushed",
    "control": "No control over recs", "freegate": "Free tier blocks discovery",
    "dj": "AI DJ problems", "newmusic": "Can't surface new releases",
    "love": "Discovery that delights", "emerging": "Other / emerging",
}
# per-PRIMARY-theme quotas (sum = 50); freegate/control weighted up (contentious boundary)
TARGETS = {"love": 6, "shuffle": 6, "freegate": 5, "control": 5, "mismatch": 5,
           "pushy": 4, "repeat": 4, "autoplay": 4, "dj": 3, "newmusic": 3,
           "safe": 3, "emerging": 2}


def primary(rec):
    th = rec.get("themes") or []
    return th[0]["theme"] if th else "emerging"


def pick(pool, k, used):
    out = []
    for r in pool:
        if len(out) >= k:
            break
        if r["review_id"] in used:
            continue
        out.append(r); used.add(r["review_id"])
    return out


def main():
    recs = [r for r in read_jsonl(C.INTERIM_DIR / "phase5_discovery_coded.jsonl")
            if r.get("discovery") and (r.get("text") or "").strip()]
    for r in recs:
        r["_prim"] = primary(r)
        r["_multi"] = len(r.get("themes") or []) >= 2
    random.shuffle(recs)

    chosen, used = [], set()
    for theme, quota in TARGETS.items():
        pool = [r for r in recs if r["_prim"] == theme]
        multi = [r for r in pool if r["_multi"]]          # boundary/ambiguous first
        single = [r for r in pool if not r["_multi"]]
        n_multi = min(len(multi), round(0.55 * quota))
        picks = pick(multi, n_multi, used)
        picks += pick(single, quota - len(picks), used)
        if len(picks) < quota:
            picks += pick(pool, quota - len(picks), used)
        chosen.extend(picks)

    random.shuffle(chosen)
    assert len(chosen) == 50, f"got {len(chosen)}"

    sheet = C.PHASES_DIR / "phase-6-gold-validation" / "gold_subtheme_sheet.csv"
    with open(sheet, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["gold_id", "rating", "review_text",
                    "your_subthemes (comma-separated codebook ids — see instructions)",
                    "repetition_type (chosen/imposed — only if shuffle/repeat/autoplay)",
                    "missing_theme (if NONE of the 11 fit, describe what's missing)",
                    "notes (optional)"])
        for i, r in enumerate(chosen, 1):
            w.writerow([i, r.get("rating"), (r.get("text") or "").strip(), "", "", "", ""])

    key = {str(i): {"review_id": r["review_id"], "rating": r.get("rating"),
                    "model_themes": [t["theme"] for t in (r.get("themes") or [])],
                    "model_snippets": [t.get("snippet") for t in (r.get("themes") or [])],
                    "model_repetition": r.get("repetition"), "coder": r.get("coder"),
                    "text": r.get("text")}
           for i, r in enumerate(chosen, 1)}
    write_json(C.PHASES_DIR / "phase-6-gold-validation" / "gold_subtheme_key.json", key)

    from collections import Counter
    pc = Counter(r["_prim"] for r in chosen)
    multi_n = sum(1 for r in chosen if r["_multi"])
    print(f"discovery sub-theme gold set: {len(chosen)} reviews -> {sheet.name}")
    print(f"  multi-theme (boundary) cases: {multi_n} / 50")
    print(f"  primary-theme coverage: {dict(pc)}")


if __name__ == "__main__":
    main()
