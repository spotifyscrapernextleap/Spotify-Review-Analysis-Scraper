"""Phase 6 (primary) — score the user-labeled DISCOVERY SUB-THEME gold set.

Compares the user's codebook sub-theme labels (truth) against the deep-coder's
predictions: overall theme accuracy (exact-set + >=1 overlap), primary-theme
accuracy, per-theme accuracy, sub-theme confusion matrix, the chosen/imposed
repetition agreement, the freegate<->control boundary, and any codebook GAPS the
user flagged via `missing_theme`. Writes `gold_subtheme_scores.json` (feeds the
contract `validation.themeAccuracy` + a sub-theme confusion exhibit).

Run (after the user fills the sheet):
  python -m phases.phase-6-gold-validation.score_subtheme_gold_set
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict

from common import config as C
from common.io import write_json

sys.stdout.reconfigure(encoding="utf-8")

DIR = C.PHASES_DIR / "phase-6-gold-validation"
THEMES = ["repeat", "shuffle", "autoplay", "safe", "mismatch", "pushy",
          "control", "freegate", "dj", "newmusic", "love", "emerging"]
VALID = set(THEMES)


def parse(raw):
    out = []
    for tok in (raw or "").replace(";", ",").replace("/", ",").split(","):
        t = tok.strip().lower()
        if t in VALID and t not in out:
            out.append(t)
    return out


def kappa(truth, pred, labels):
    n = len(truth)
    if not n:
        return 0.0
    po = sum(1 for t, p in zip(truth, pred) if t == p) / n
    tc, pc = Counter(truth), Counter(pred)
    pe = sum((tc[l] / n) * (pc[l] / n) for l in labels)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def main():
    key = json.load(open(DIR / "gold_subtheme_key.json", encoding="utf-8"))
    filled = {}
    with open(DIR / "gold_subtheme_sheet.csv", encoding="utf-8-sig", newline="") as fh:
        r = csv.DictReader(fh)
        cols = r.fieldnames
        sub_c = next(c for c in cols if c.startswith("your_subthemes"))
        rep_c = next(c for c in cols if c.startswith("repetition_type"))
        miss_c = next(c for c in cols if c.startswith("missing_theme"))
        for row in r:
            gid = (row.get("gold_id") or "").strip()
            if gid:
                filled[gid] = {"themes": parse(row.get(sub_c)),
                               "raw": (row.get(sub_c) or "").strip(),
                               "rep": (row.get(rep_c) or "").strip().lower(),
                               "missing": (row.get(miss_c) or "").strip()}

    # rows the user marked with NO valid codebook theme (e.g. "na", "tech error") =
    # the user disagreeing the review is discovery at all (model false-positive / data
    # leak). Score the codebook FIT on genuine-discovery rows; report these separately.
    not_discovery = [{"gold_id": g, "user_raw": filled[g]["raw"],
                      "model_themes": key[g].get("model_themes"),
                      "text": (key[g].get("text") or "")[:150]}
                     for g in key if filled.get(g) and not filled[g]["themes"]]

    n = exact = overlap = primary_hit = rep_n = rep_hit = 0
    t_prim, p_prim = [], []
    per_theme = defaultdict(lambda: [0, 0])     # truth primary -> [hits,total]
    gaps = []
    boundary = {"user_freegate_model": Counter(), "user_control_model": Counter()}
    for gid, k in key.items():
        u = filled.get(gid)
        if not u or not u["themes"]:
            continue
        n += 1
        model = k.get("model_themes") or ["emerging"]
        uset, mset = set(u["themes"]), set(model)
        exact += (uset == mset)
        overlap += bool(uset & mset)
        up, mp = u["themes"][0], (model[0] if model else "emerging")
        t_prim.append(up); p_prim.append(mp)
        primary_hit += (up == mp)
        per_theme[up][0] += (up == mp); per_theme[up][1] += 1
        if u["rep"] in ("chosen", "imposed") and k.get("model_repetition"):
            rep_n += 1; rep_hit += (u["rep"] == k["model_repetition"])
        if "freegate" in uset:
            boundary["user_freegate_model"].update(model)
        if "control" in uset:
            boundary["user_control_model"].update(model)

    # codebook gaps: every row where the user wrote a missing_theme note (incl. not_discovery rows)
    gaps = [{"gold_id": g, "missing": filled[g]["missing"], "user": filled[g]["raw"],
             "text": (key[g].get("text") or "")[:160]}
            for g in key if filled.get(g) and filled[g]["missing"]]

    def pct(a, b):
        return round(100 * a / b, 1) if b else None

    labels = [l for l in THEMES if l in set(t_prim) | set(p_prim)]
    idx = {l: i for i, l in enumerate(labels)}
    mat = [[0] * len(labels) for _ in labels]
    for t, p in zip(t_prim, p_prim):
        mat[idx[t]][idx[p]] += 1

    out = {
        "n_scored": n,
        "themeAccuracy_exactSet": pct(exact, n),
        "themeAccuracy_overlap": pct(overlap, n),
        "primaryThemeAccuracy": pct(primary_hit, n),
        "kappa_primary": kappa(t_prim, p_prim, labels),
        "repetitionTypeAgreement": {"n": rep_n, "agreement": pct(rep_hit, rep_n)},
        "perThemeAccuracy": {t: {"acc": pct(h, tot), "n": tot} for t, (h, tot) in sorted(per_theme.items())},
        "confusion": {"labels": labels, "matrix_counts": mat},
        "freegateControlBoundary": {"user_freegate_modelSaid": dict(boundary["user_freegate_model"]),
                                    "user_control_modelSaid": dict(boundary["user_control_model"])},
        "codebookGaps_flagged": gaps,
        "notDiscovery_userFlagged": not_discovery,
    }
    write_json(DIR / "gold_subtheme_scores.json", out)
    print("========== DISCOVERY SUB-THEME VALIDATION ==========")
    print(f"scored {n}/50  (codebook fit measured on genuine-discovery rows)")
    if not_discovery:
        print(f"  + {len(not_discovery)} rows you flagged as NOT a codebook theme (excluded from accuracy):")
        for d in not_discovery:
            print(f"      #{d['gold_id']} you='{d['user_raw']}'  model={d['model_themes']}  <- {d['text'][:65]}")
    print(f"  theme accuracy (>=1 overlap)   : {out['themeAccuracy_overlap']}%")
    print(f"  theme accuracy (exact set)     : {out['themeAccuracy_exactSet']}%")
    print(f"  primary-theme accuracy         : {out['primaryThemeAccuracy']}%")
    print(f"  kappa (primary)                : {out['kappa_primary']}")
    print(f"  chosen/imposed agreement       : {out['repetitionTypeAgreement']['agreement']}% (n={rep_n})")
    print("\n  per-theme accuracy (truth = your primary):")
    for t, d in out["perThemeAccuracy"].items():
        print(f"    {t:10s} {str(d['acc']):>5}%  (n={d['n']})")
    if gaps:
        print(f"\n  ⚠ codebook GAPS you flagged ({len(gaps)}):")
        for g in gaps:
            print(f"    #{g['gold_id']}: '{g['missing']}'  <- {g['text'][:70]}")
    else:
        print("\n  no codebook gaps flagged (every review fit the 11 themes)")


if __name__ == "__main__":
    main()
