"""Phase 6 — score the user-labeled gold set against the model's predictions.

Reads the filled `gold_labeling_sheet.csv` (user truth) + `gold_key.json` (model
predictions) and computes: overall accuracy (exact-set + at-least-one-overlap),
per-category accuracy, Cohen's kappa (on primary label), confusion matrix,
sentiment accuracy, abstention calibration (high vs low model confidence), and
gold-set composition. Writes `gold_scores.json` (feeds contract `validation`,
`evaluation.confusion`, `evaluation.goldComposition`, `evaluation.abstention`).

Run (after the user fills the sheet):
  python -m phases.phase-6-gold-validation.score_gold_set
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict

from common import config as C
from common.io import write_json

sys.stdout.reconfigure(encoding="utf-8")

DIR = C.PHASES_DIR / "phase-6-gold-validation"
VALID = set(C.CATEGORY_IDS) | {"none"}
ORDER = C.CATEGORY_IDS + ["none"]   # confusion/kappa label order


def parse_cats(raw: str):
    """User cell -> normalised list of valid category ids (order preserved)."""
    out = []
    for tok in (raw or "").replace(";", ",").replace("/", ",").split(","):
        t = tok.strip().lower()
        if t in VALID and t not in out:
            out.append(t)
    return out or ["none"]


def load_filled():
    import json
    key = json.load(open(DIR / "gold_key.json", encoding="utf-8"))
    rows = {}
    with open(DIR / "gold_labeling_sheet.csv", encoding="utf-8-sig", newline="") as fh:
        r = csv.DictReader(fh)
        cols = r.fieldnames
        cat_col = next(c for c in cols if c.startswith("label_categories"))
        sent_col = next(c for c in cols if c.startswith("label_sentiment"))
        for row in r:
            gid = (row.get("gold_id") or "").strip()
            if gid:
                rows[gid] = {"cats": parse_cats(row.get(cat_col)),
                             "sent": (row.get(sent_col) or "").strip().lower()}
    return key, rows


def kappa(truth, pred, labels):
    n = len(truth)
    if not n:
        return 0.0
    po = sum(1 for t, p in zip(truth, pred) if t == p) / n
    tc, pc = Counter(truth), Counter(pred)
    pe = sum((tc[l] / n) * (pc[l] / n) for l in labels)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def main():
    key, filled = load_filled()
    unfilled = [g for g in key if not filled.get(g) or filled[g]["cats"] == ["none"]
                and not (filled.get(g))]
    missing = [g for g in key if g not in filled or not filled[g]["cats"]]
    if missing:
        print(f"WARNING: {len(missing)} rows look unlabeled: {missing[:10]}")

    exact = overlap = primary_hit = sent_hit = 0
    t_primary, p_primary = [], []
    per_cat_truth = defaultdict(lambda: [0, 0])   # cat -> [hits, total] by user-primary
    conf_buckets = {"high": [0, 0], "low": [0, 0]}  # model_confidence -> [hits, total]
    comp = {"borderline": [0, 0], "easy": [0, 0]}
    n = 0
    for gid, k in key.items():
        u = filled.get(gid)
        if not u or not u["cats"]:
            continue
        n += 1
        model = [c for c in (k["model_categories"] or ["none"])]
        uset, mset = set(u["cats"]), set(model)
        if uset == mset:
            exact += 1
        if uset & mset:
            overlap += 1
        up, mp = u["cats"][0], model[0]
        t_primary.append(up); p_primary.append(mp)
        hit = (up == mp)
        primary_hit += hit
        per_cat_truth[up][0] += hit; per_cat_truth[up][1] += 1
        if k.get("model_sentiment") and u["sent"]:
            sent_hit += (k["model_sentiment"] == u["sent"])
        cb = conf_buckets["high" if k.get("model_confidence") == "high" else "low"]
        cb[0] += hit; cb[1] += 1
        bt = "easy" if k.get("borderline_type") == "easy" else "borderline"
        comp[bt][0] += hit; comp[bt][1] += 1

    def pct(a, b):
        return round(100 * a / b, 1) if b else None

    # confusion matrix (rows=truth primary, cols=pred primary), % per truth row
    labels = [l for l in ORDER if l in set(t_primary) | set(p_primary)]
    idx = {l: i for i, l in enumerate(labels)}
    mat = [[0] * len(labels) for _ in labels]
    for t, p in zip(t_primary, p_primary):
        mat[idx[t]][idx[p]] += 1
    mat_pct = [[round(100 * c / max(sum(row), 1), 1) for c in row] for row in mat]

    out = {
        "n_scored": n,
        "overallAccuracy_exactSet": pct(exact, n),
        "overallAccuracy_overlap": pct(overlap, n),
        "primaryLabelAccuracy": pct(primary_hit, n),
        "sentimentAccuracy": pct(sent_hit, n),
        "kappa_primary": kappa(t_primary, p_primary, labels),
        "perCategoryAccuracy": {c: {"acc": pct(h, t), "n": t} for c, (h, t) in sorted(per_cat_truth.items())},
        "confusion": {"labels": labels, "matrix_counts": mat, "matrix_pct": mat_pct,
                      "discoveryAccuracy": pct(*per_cat_truth.get("discovery", [0, 0]))},
        "abstention": {
            "confidentShare": pct(conf_buckets["high"][1], n),
            "confidentAccuracy": pct(*conf_buckets["high"]),
            "lowConfShare": pct(conf_buckets["low"][1], n),
            "lowConfAccuracy": pct(*conf_buckets["low"]),
        },
        "goldComposition": {
            "total": n, "borderline": comp["borderline"][1], "easy": comp["easy"][1],
            "borderlineAccuracy": pct(*comp["borderline"]),
            "easyAccuracy": pct(*comp["easy"]),
            "coverage": [{"cat": c, "count": t} for c, (_, t) in sorted(per_cat_truth.items())],
        },
    }
    write_json(DIR / "gold_scores.json", out)
    print("========== GOLD-SET VALIDATION ==========")
    print(f"scored {n}/50")
    print(f"  overall accuracy (exact category-set match): {out['overallAccuracy_exactSet']}%")
    print(f"  overall accuracy (>=1 category overlap)     : {out['overallAccuracy_overlap']}%")
    print(f"  primary-label accuracy                      : {out['primaryLabelAccuracy']}%")
    print(f"  Cohen's kappa (primary)                     : {out['kappa_primary']}")
    print(f"  sentiment accuracy                          : {out['sentimentAccuracy']}%")
    print(f"  discovery accuracy                          : {out['confusion']['discoveryAccuracy']}%")
    print("\n  per-category accuracy (truth = your primary label):")
    for c, d in out["perCategoryAccuracy"].items():
        print(f"    {c:10s} {str(d['acc']):>5}%  (n={d['n']})")
    print("\n  abstention calibration:")
    print(f"    high-confidence: {out['abstention']['confidentAccuracy']}% acc  ({out['abstention']['confidentShare']}% of set)")
    print(f"    low-confidence : {out['abstention']['lowConfAccuracy']}% acc  ({out['abstention']['lowConfShare']}% of set)")
    print(f"\n  borderline acc {out['goldComposition']['borderlineAccuracy']}% (n={out['goldComposition']['borderline']})"
          f"  vs easy acc {out['goldComposition']['easyAccuracy']}% (n={out['goldComposition']['easy']})")


if __name__ == "__main__":
    main()
