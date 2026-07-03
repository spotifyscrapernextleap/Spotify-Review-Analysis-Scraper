# Phase 6 — Gold Validation (iOS track)

**Objective:** validate the codebook-v3 discovery sub-theme coding against a small,
**user-labeled** (not model-labeled — this is the *gold* set, distinct from the *golden* set
used to test the deterministic filter, see Android's gotchas list) iOS-specific sheet.

**Scope decision:** ~25 reviews (half the Android 50-review discovery sub-theme gold set) —
lighter labeling load, wider error bars on the resulting accuracy numbers, but still enough to
catch systematic miscoding (a theme collapsing into the wrong bucket, a guardrail failing to
fire) rather than a precise per-theme accuracy figure. Broad-category (Layer-1) gold
validation is **not** planned for iOS, mirroring Android's decision to park 6B in favour of
the Phase-4 recall probe/recovery as the Layer-1 check (D12).

**Inputs:** `data/interim/ios_recode_v3_coded.jsonl` (Phase 5 output).

**Steps (planned, adapting `phases/phase-6-gold-validation/build_subtheme_gold_set.py` /
`score_subtheme_gold_set.py`):**
1. `build_subtheme_gold_set_ios.py` → `gold_subtheme_sheet_ios.csv` (~25 reviews, blind,
   stratified across the 10 v3 themes + emerging), `gold_subtheme_key_ios.json` (hidden).
2. **🏷️ Human checkpoint — user labels `gold_subtheme_sheet_ios.csv`.**
3. `score_subtheme_gold_set_ios.py` → theme accuracy, per-theme accuracy, kappa, sub-theme
   confusion, chosen/imposed agreement.

**Outputs (planned):** `gold_subtheme_sheet_ios.csv`, `gold_subtheme_key_ios.json`,
`gold_subtheme_scores_ios.json`.

**Contract fields produced:** `validation.themeAccuracy` (iOS), an iOS sub-theme confusion
exhibit for the Methodology section (if/when the iOS track is wired into the dashboard).

**Status:** not yet built — depends on Phase 5 (iOS discovery deep-coding) completing first.

**Checkpoints / human input:** 🏷️ the ~25-review labeling pass — the only step in the iOS
track that requires user input.
