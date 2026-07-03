# Phase 6 — Gold Set & Validation 🏷️

Two validations. The **discovery sub-theme** set is the **priority** (it validates the
codebook that answers the six questions); the **broad-category** set is **parked**
(optional — only feeds the methodology confusion matrix).

## 6A — Discovery sub-theme gold set  ← ACTIVE / PRIORITY
**Validates Layer-2:** do the 11 codebook sub-themes fit the 1,792 discovery reviews?
- `build_subtheme_gold_set.py` → `gold_subtheme_sheet.csv` (50 reviews, blind; 24 multi-theme
  boundary cases; all 11 themes + emerging covered), `gold_subtheme_key.json` (HIDDEN).
- `gold_subtheme_instructions.md` — the codebook rubric + how to flag codebook gaps.
- **🏷️ User labels `gold_subtheme_sheet.csv`** ← AWAITING USER.
- `score_subtheme_gold_set.py` → theme accuracy, per-theme accuracy, kappa, sub-theme
  confusion, chosen/imposed agreement, flagged codebook gaps. **Built + smoke-tested.**
- **Contract fields:** `validation.themeAccuracy`, a sub-theme confusion exhibit.

## 6B — Broad-category gold set  ← PARKED (optional)
**Validates Layer-1:** the 8B's broad sort (discovery vs pricing/tech/ux/...). Only needed
for the methodology **confusion matrix** (`evaluation.confusion`) + `validation.categoryAccuracy`.
The discovery boundary was already validated via the Phase-4 recall probe + recovery, so this
is secondary. Built and ready if/when we want it:
- `build_gold_set.py` → `gold_labeling_sheet.csv` + `gold_key.json`; `gold_labeling_instructions.md`;
  `score_gold_set.py` (built + smoke-tested).

**Run the builds:**
```
./.venv/Scripts/python.exe -m phases.phase-6-gold-validation.build_subtheme_gold_set   # 6A (priority)
./.venv/Scripts/python.exe -m phases.phase-6-gold-validation.build_gold_set            # 6B (parked)
```
