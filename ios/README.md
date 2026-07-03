# iOS track

This folder holds every piece of code that is **iOS-specific** for the Spotify Review
Intelligence pipeline, laid out with the same `phase-N-name/` convention as `phases/`
(Android's track) — see each subfolder's `README.md` for Objective/Inputs/Steps/Outputs/
Contract-fields/How-to-re-run, matching the Android phase docs.

**Why a separate folder instead of one shared `phases/` tree:** Android and iOS are two
independently-built pipelines producing two separate snapshots of the same schema (D1 in
`PROJECT_MEMORY.md`) — the two store feeds expose fundamentally different depths. Android's
`google-play-scraper` deep-paginates, so it census-scrapes a real 6-month window. iOS's
iTunes RSS feed hard-caps at ~500 reviews/country ≈ 2–3 weeks (page 11 → HTTP 400, expected),
so it can only ever be a **current snapshot** — census-classified (not sampled), with no
trend/window dimension. The two tracks' numbers must never be blended into one cross-platform
figure (EC-34).

## What's genuinely iOS-only vs. reused

Two different things live under `ios/`, and it matters which is which:

- **Code that is exclusively iOS's** (no Android coupling at all) lives here as real files —
  e.g. `phase-1-collection/scout_ios.py` and `collect_ios.py`.
- **Code that already handles both tracks via a `track` argument** — `filter_reviews.py`
  (Phase 2) and `classify.py` (Phase 4 broad) — stays in `phases/`, invoked with `track=ios`.
  These are single scripts by design (D6/D9 in `PROJECT_MEMORY.md`): the whole point of
  parameterising by track is that both tracks apply the *exact same* filtering rules and the
  *exact same* hardened v5 classification prompt, so there's no drift between what "pricing"
  or "discovery" means on Android vs. iOS. Forking copies of these into `ios/` would
  reintroduce that drift risk. Each `ios/phase-N/README.md` says explicitly which case it is.

## Phase status

| Phase | Status | Notes |
|---|---|---|
| `phase-1-collection/` | ✅ done | 2,500 raw across US/GB/CA/IN/AU |
| `phase-2-filtering/` | ✅ done | 2,106 substantive candidates (reuses shared `filter_reviews.py`) |
| `phase-3-window/` | N/A | iOS has no time series — see that folder's README |
| `phase-4-layer1-broad/` | not yet run | census-classify 2,106 candidates (reuses shared `classify.py`); recall-recovery script planned |
| `phase-5-layer2-discovery/` | not yet built | codebook-v3 deep coding on gpt-oss-120b, adapted from Android's `recode_v3.py` |
| `phase-6-gold-validation/` | not yet built | ~25-review user-labeled gold sheet 🏷️ — the one step needing your input |
| `phase-7-analysis-snapshot/` | not yet built | emits `data/REVIEW_DATA.ios.json`, census-exact, no window/trend |

**Current scope boundary:** this build-out ends at a contract-valid
`data/REVIEW_DATA.ios.json`. Wiring it into the Phase-8 dashboard (platform toggle or second
page) is a separate, later effort.

See `PROJECT_MEMORY.md` (repo root) §7 for the authoritative up-to-date status of this track.
