"""Phase 6 (iOS) — build the iOS DISCOVERY SUB-THEME gold set (~25 reviews).

iOS analogue of phases/phase-6-gold-validation/build_subtheme_gold_set.py, but:
  - validates against codebook **v3** (10 themes + emerging; autoplay/safe RETIRED,
    smartrec present) — the same rubric ios recode_v3_ios.py used;
  - ~25 reviews (half the Android 50) per the user's scope choice — lighter labeling
    load, catches systematic miscoding rather than a precise per-theme figure;
  - samples from data/interim/ios_recode_v3_coded.jsonl (the iOS deep-coded pool);
  - backfills any theme shortfall from the rest of the pool so we still reach the
    target even if some v3 themes are sparse in the smaller iOS corpus.

The user labels each review with the codebook sub-theme(s) it really raises and can flag
reviews the codebook MISSES. Model predictions stay in a hidden key so labeling is blind.

Run:
  python -m ios.phase-6-gold-validation.build_subtheme_gold_set_ios [--target 25]
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter

from common import config as C
from common.io import read_jsonl, write_json

sys.stdout.reconfigure(encoding="utf-8")   # Windows cp1252 console crashes on non-ASCII (project gotcha)
random.seed(42)
DIR = C.ROOT / "ios" / "phase-6-gold-validation"

# v3 codebook (autoplay/safe retired, smartrec present) + emerging
NAMES = {
    "repeat": "Same songs on repeat", "shuffle": "Shuffle isn't random",
    "mismatch": "Irrelevant / wrong recs", "pushy": "Unwanted recs pushed",
    "smartrec": "Wants smarter / personalized recs",
    "control": "No control over recs", "freegate": "Free tier blocks discovery",
    "dj": "AI DJ problems", "newmusic": "Can't surface new releases",
    "love": "Discovery that delights", "emerging": "Other / emerging",
}
# per-PRIMARY-theme quotas (sum = 25); control/freegate/shuffle weighted up
# (contentious boundaries — control<->pushy<->repeat, freegate<->shuffle<->control).
TARGETS = {"control": 4, "love": 3, "shuffle": 3, "freegate": 3, "mismatch": 2,
           "pushy": 2, "repeat": 2, "smartrec": 2, "dj": 1, "newmusic": 1, "emerging": 2}


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


def main(target):
    src = C.INTERIM_DIR / "ios_recode_v3_coded.jsonl"
    if not src.exists():
        raise SystemExit(f"Missing {src} — run recode_v3_ios.py first.")
    recs = [r for r in read_jsonl(src)
            if r.get("discovery") and (r.get("text") or "").strip()]
    if len(recs) < target:
        raise SystemExit(f"Only {len(recs)} discovery reviews coded — need >= {target}.")
    for r in recs:
        r["_prim"] = primary(r)
        r["_multi"] = len(r.get("themes") or []) >= 2
    random.shuffle(recs)

    # scale quotas to the requested target (defaults sum to 25)
    scale = target / sum(TARGETS.values())
    quotas = {t: max(1, round(q * scale)) for t, q in TARGETS.items()}

    chosen, used = [], set()
    for theme, quota in quotas.items():
        pool = [r for r in recs if r["_prim"] == theme]
        multi = [r for r in pool if r["_multi"]]           # boundary/ambiguous first
        single = [r for r in pool if not r["_multi"]]
        n_multi = min(len(multi), round(0.55 * quota))
        picks = pick(multi, n_multi, used)
        picks += pick(single, quota - len(picks), used)
        if len(picks) < quota:
            picks += pick(pool, quota - len(picks), used)
        chosen.extend(picks)

    # backfill/trim to EXACTLY target — sparse themes may have under-filled.
    if len(chosen) < target:
        remaining = [r for r in recs if r["review_id"] not in used]
        remaining.sort(key=lambda r: (not r["_multi"],))    # boundary cases first
        chosen += pick(remaining, target - len(chosen), used)
    chosen = chosen[:target]
    random.shuffle(chosen)

    DIR.mkdir(parents=True, exist_ok=True)
    sheet = DIR / "gold_subtheme_sheet_ios.csv"
    with open(sheet, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["gold_id", "rating", "country", "review_text",
                    "your_subthemes (comma-separated codebook ids — see instructions)",
                    "repetition_type (chosen/imposed — only if shuffle/repeat)",
                    "missing_theme (if NONE of the 10 fit, describe what's missing)",
                    "notes (optional)"])
        for i, r in enumerate(chosen, 1):
            w.writerow([i, r.get("rating"), (r.get("country") or "").upper(),
                        (r.get("text") or "").strip(), "", "", "", ""])

    key = {str(i): {"review_id": r["review_id"], "rating": r.get("rating"),
                    "country": r.get("country"),
                    "model_themes": [t["theme"] for t in (r.get("themes") or [])],
                    "model_snippets": [t.get("snippet") for t in (r.get("themes") or [])],
                    "model_repetition": r.get("repetition"), "coder": r.get("coder"),
                    "text": r.get("text")}
           for i, r in enumerate(chosen, 1)}
    write_json(DIR / "gold_subtheme_key_ios.json", key)

    pc = Counter(r["_prim"] for r in chosen)
    multi_n = sum(1 for r in chosen if r["_multi"])
    print(f"iOS discovery sub-theme gold set: {len(chosen)} reviews -> {sheet.name}")
    print(f"  multi-theme (boundary) cases: {multi_n} / {len(chosen)}")
    print(f"  primary-theme coverage: {dict(pc)}")
    print(f"\n  🏷️  Label the '{sheet.name}' column 'your_subthemes' (see gold_subtheme_instructions_ios.md),")
    print(f"     then run:  python -m ios.phase-6-gold-validation.score_subtheme_gold_set_ios")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=25)
    a = p.parse_args()
    main(a.target)
