"""Phase 6 — build the 50-review GOLD SET labeling sheet.

Validity rule (D10): the gold labels must be the USER's, made WITHOUT seeing the
classifier's predictions. So this writes:
  - gold_labeling_sheet.csv      — text only + blank label columns (what the user fills)
  - gold_key.json                — HIDDEN: model predictions + borderline type (user must NOT open)
  - gold_labeling_instructions.md — the category definitions + how to label

Selection: 50 reviews stratified across all 8 categories (by the model's PREDICTED
primary category, to guarantee coverage), deliberately weighted toward BORDERLINE
cases (short-but-substantive, long-but-empty, low-confidence, multi-label) so the
accuracy number isn't flattered by easy examples.

Run:
  python -m phases.phase-6-gold-validation.build_gold_set
"""
from __future__ import annotations

import csv
import json
import random

from common import config as C
from common.io import read_jsonl, write_json

random.seed(42)

# per-PREDICTED-category quotas (sum = 50); discovery weighted up (headline category)
TARGETS = {"discovery": 10, "pricing": 8, "tech": 7, "ux": 7,
           "catalogue": 5, "audio": 4, "updates": 4, "none": 5}
BORDERLINE_FRAC = 0.64  # ~32/50 borderline, ~18/50 easy


def borderline_type(rec) -> str:
    L = len(rec.get("text") or "")
    cats = rec.get("categories") or []
    conf = rec.get("confidence")
    if cats != ["none"] and L <= 75:
        return "short_substantive"
    if cats == ["none"] and L >= 180:
        return "long_empty"
    if conf == "low":
        return "low_conf"
    if len(cats) >= 2:
        return "multi_label"
    return "easy"


def primary(rec) -> str:
    cats = rec.get("categories") or ["none"]
    return cats[0]


def pick(pool, k, exclude_ids):
    out = []
    for r in pool:
        if len(out) >= k:
            break
        if r["review_id"] in exclude_ids:
            continue
        out.append(r)
        exclude_ids.add(r["review_id"])
    return out


def main():
    rows = list(read_jsonl(C.INTERIM_DIR / "android_layer1.jsonl"))
    # only reviews with some text; dedupe identical text to avoid trivial repeats
    rows = [r for r in rows if (r.get("text") or "").strip()]
    for r in rows:
        r["_bt"] = borderline_type(r)
        r["_prim"] = primary(r)
    random.shuffle(rows)

    chosen, used = [], set()
    for cat, quota in TARGETS.items():
        cat_pool = [r for r in rows if r["_prim"] == cat]
        n_border = round(BORDERLINE_FRAC * quota)
        # favour the two brief-named borderline types (long-but-empty, short-but-substantive);
        # rows is pre-shuffled so the stable sort keeps randomness within each tier.
        _pri = {"long_empty": 0, "short_substantive": 1, "multi_label": 2, "low_conf": 3}
        border_pool = sorted([r for r in cat_pool if r["_bt"] != "easy"],
                             key=lambda r: _pri.get(r["_bt"], 9))
        easy_pool = [r for r in cat_pool if r["_bt"] == "easy"]
        picks = pick(border_pool, n_border, used)
        picks += pick(easy_pool, quota - len(picks), used)
        if len(picks) < quota:  # backfill from whichever pool has more
            picks += pick(cat_pool, quota - len(picks), used)
        chosen.extend(picks)

    random.shuffle(chosen)  # interleave categories so the user can't pattern-label
    assert len(chosen) == 50, f"got {len(chosen)} (check pools)"

    # write the blind labeling sheet (utf-8-sig so Excel renders emoji/unicode)
    sheet = C.PHASES_DIR / "phase-6-gold-validation" / "gold_labeling_sheet.csv"
    with open(sheet, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["gold_id", "rating", "review_text",
                    "label_categories (comma-separated, see instructions)",
                    "label_sentiment (positive/negative/mixed)", "notes (optional)"])
        for i, r in enumerate(chosen, 1):
            w.writerow([i, r.get("rating"), (r.get("text") or "").strip(), "", "", ""])

    # hidden key — model predictions + borderline type, NEVER shown to the labeler
    key = {str(i): {"review_id": r["review_id"], "rating": r.get("rating"),
                    "model_categories": r.get("categories"), "model_sentiment": r.get("sentiment"),
                    "model_confidence": r.get("confidence"), "borderline_type": r["_bt"],
                    "text": r.get("text")}
           for i, r in enumerate(chosen, 1)}
    write_json(C.PHASES_DIR / "phase-6-gold-validation" / "gold_key.json", key)

    # report composition
    from collections import Counter
    bt = Counter(r["_bt"] for r in chosen)
    pc = Counter(r["_prim"] for r in chosen)
    print(f"gold set: {len(chosen)} reviews -> {sheet.name}")
    print(f"  borderline mix: {dict(bt)}")
    print(f"  easy={bt['easy']}  borderline={50 - bt['easy']}")
    print(f"  predicted-category coverage: {dict(pc)}")


if __name__ == "__main__":
    main()
