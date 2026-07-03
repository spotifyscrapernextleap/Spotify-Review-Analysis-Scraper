# Phase 2 — Normalisation & Filtering (iOS track)

**Objective:** deterministically clean the raw iOS corpus into Tier A/B/C — routing, never
deleting. No model involved.

**Code location — reused, not forked:** this phase's logic
(`phases/phase-2-filtering/filter_reviews.py`) is a **single script parameterised by track**
(`filter_reviews.py <android|ios>`), not two separate implementations. It runs the exact same
field-integrity / dedupe / language / junk-routing rules for both tracks, so there is nothing
iOS-specific to fork here — forking it would just risk the two tracks' filtering silently
drifting apart. See `phases/phase-2-filtering/README.md` for the full step-by-step and Android
numbers.

**Inputs:** `data/raw/ios_raw.jsonl` + `ios_manifest.json` (`ios/phase-1-collection/`);
`phases/phase-0-foundations/golden_set.jsonl`.

**Outputs:** `data/interim/ios/{substantive_candidates,tierC,quarantined}.jsonl`,
`data/interim/ios_filter_report.json`.

**iOS funnel result** (snapshot, not census — see `ios/phase-1-collection/README.md`):
collected 2,500 → id-dedup 2,500 (0 — iOS reviewIds are genuinely per-storefront, unlike
Android) → english 2,398 (−102 non-English) → **substantive candidates 2,106** + Tier C 292.

**Exit criteria:** ✅ golden test passes (shared with Android); funnel reconciles.

**Checkpoints / human input:** none.

**How to re-run:**
```bash
./.venv/Scripts/python.exe -m phases.phase-2-filtering.filter_reviews ios
```
