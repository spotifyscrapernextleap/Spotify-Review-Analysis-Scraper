# Phase 1 — Collection (Android track)

**Objective:** collect the Android review corpus. Android and iOS are built as two
independently-scraped tracks — see `ios/phase-1-collection/README.md` for the iOS side
and `ios/README.md` for why the tracks are split.

> **Why two tracks (the wall):** Spotify's review velocity (~770 Android reviews/country/day)
> means the public feeds only surface a recent sliver. Tests:
> - **Android** deep-paginates — 10k reviews reached 13 days back; pagination continues. So a
>   real **6-month** census scrape is possible (heavy but feasible).
> - **iOS** RSS **hard-caps at 500/country ≈ 2–3 weeks** (page 11 → HTTP 400). It can *never*
>   go deeper. So iOS is a **current snapshot**, not a time series — built under `ios/`.

## Track A — Android (`collect_android.py`)
- **Scope:** US, GB, IN · **deep-collect 6 months** (`Sort.NEWEST`, page until the 6-month cutoff; no count cap, 200k/country safety guard).
- **Why census-scrape the whole window:** holding the full month populations (not a sorted slice) is what makes later month-stratified LLM sampling statistically valid.
- **Outputs:** `data/raw/android_raw.jsonl`, `data/raw/android_manifest.json` (counts by country × month — the volume-over-time backbone).

**Tests run:**
- Scraper validated on small runs before the full pull.
- EC-1 date-span probe (Android 13d/10k) — drove the two-track split (see `ios/README.md` for the iOS-side probe).

**Result:** Android ~6-month deep corpus.

**Exit criteria:** ✅ Android census scrape covers the 6-month window with reconciling manifest.

**Checkpoints / human input:** none (scope locked with the user).

**How to re-run:**
```bash
./.venv/Scripts/python.exe -m phases.phase-1-collection.collect_android   # ~40 min
```
