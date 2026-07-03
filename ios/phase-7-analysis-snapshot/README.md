# Phase 7 — Analysis Snapshot (iOS track)

**Objective:** compute every metric and emit the iOS `window.REVIEW_DATA` snapshot,
validated against the same `common/contract.py` schema Android uses.

**Census-exact, not projected (D3/D14):** unlike Android, where category/substantive/
discovery counts are stratified-sample estimates projected to the population ± margin of
error, iOS classified its **entire** substantive-candidate pile (Phase 4 is a census, not a
sample). So every iOS number in the snapshot — collection, dedup, English, category counts,
discovery counts — is **exact**, no MoE, no bootstrap CI needed for the effect size.

**No window/trend (D11):** iOS has no monthly time dimension (Phase 3 is N/A for this track
— see `ios/phase-3-window/README.md`). The snapshot's `window` field carries a short
"current snapshot, ~2-3 week span" justification string instead of the Android
`trends`/`trendDirection` monthly series; `platforms.ios` in the contract is populated,
`trends` stays empty or omitted for this track.

**Inputs:**
- `data/interim/ios_filter_report.json` (Phase 2 census funnel)
- `data/interim/ios_layer1.jsonl` (Phase 4 census classification)
- `data/interim/ios_recode_v3_analysis.json` (Phase 5 discovery deep-dive)
- `data/interim/gold_subtheme_scores_ios.json` (Phase 6 validation)

**Status:** not yet built. Will be `build_snapshot_ios.py` — a track-adapted copy of
`phases/phase-7-analysis-snapshot/build_snapshot.py`, dropping the sample-projection math
(no `PROJ_*` fields — iOS numbers are already exact) and the window/trend assembly.

**Outputs (planned):** `data/REVIEW_DATA.ios.json` — validated via
`python -m common.contract data/REVIEW_DATA.ios.json`.

**⚠️ Never merged with Android:** the two tracks cover different time spans (6-month deep
census vs. ~2-3 week snapshot) and must stay two separate snapshot files — no blended
cross-platform number (D1, EC-34).

**Scope boundary:** this phase is the current end point for the iOS track. Wiring
`REVIEW_DATA.ios.json` into the Phase-8 dashboard (a platform toggle or second page) is
explicitly a separate, later effort — not part of this build-out.

**How to run (once built):**
```bash
./.venv/Scripts/python.exe -m ios.phase-7-analysis-snapshot.build_snapshot_ios
```
