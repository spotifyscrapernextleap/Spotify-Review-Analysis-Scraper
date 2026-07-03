# Phase 7 — Analysis, Metrics & Snapshot Emission

**Objective:** compute every number the dashboard shows and emit the validated
Android `window.REVIEW_DATA` snapshot.

**Inputs:** census funnel/window (`android_filter_report.json`, `android_window.json`),
Layer-1 sample (`android_layer1.jsonl`), Claude re-code of discovery
(`phase5_recode_*`), model deep-code (`phase5_discovery_analysis.json`),
gold-set scores (`phase-6/gold_subtheme_scores.json`).

**Steps:** `build_snapshot.py` computes — category share of voice (projected),
census star baseline, effect size + 2,000-sample **bootstrap CI**, monthly discovery
trend + direction, discovery themes/repetition-cluster/bridge/buckets (from the
re-code), behaviours/segments/unmet-needs, delight, per-category sentiment split,
real evidence quotes per theme, validation metrics, and the 7 evaluation exhibits —
then assembles and **validates against `common/contract.py`** (pydantic + cross-checks).

**Output:** `data/REVIEW_DATA.android.json` — passes `python -m common.contract`.

**Headline numbers (Android):**
- Funnel: 387,086 collected → 124,597 English → ~54,564 substantive (projected) → ~9,716 discovery → 687 deep-coded.
- Share of voice (of substantive): **pricing 52.8%, tech 18.7%, discovery 17.8%**, ux 11.8%, updates 6.2%, catalogue 5.0%, audio 4.2%, other 1.0%.
- Effect size: discovery **3.35★ vs 3.78★ baseline = −0.43 (95% CI [−0.50, −0.36])**.
- Discovery is **control-dominated**: control / freegate / pushy / shuffle (forced playback) outweigh recommendation-quality themes; repetition is **100% imposed**; `love` ≈ 40% positive.
- Validation: 73% sub-theme agreement, kappa 0.33 (see limitations).

**Census exact vs sample-projected:** collection, dedup, English filter, star
baseline, and monthly volume are census-exact; substantive/category/discovery counts
are stratified-sample estimates projected to the population (± MoE). Stated in `limitations`.

**Not yet:** iOS track (Layer-1 pending) → a second snapshot of the same schema.

**How to re-run:** `./.venv/Scripts/python.exe -m phases.phase-7-analysis-snapshot.build_snapshot`
