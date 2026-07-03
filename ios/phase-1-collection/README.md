# Phase 1 — Collection (iOS track)

**Objective:** collect the iOS review corpus. iOS is built as an independent track from
Android — see `phases/phase-1-collection/README.md` for the Android side and `ios/README.md`
for the full rationale.

> **Why iOS is a snapshot, not a time series:** the iTunes RSS customer-reviews feed
> **hard-caps at ~10 pages × 50 = 500 reviews/country** (page 11 → HTTP 400/500, expected —
> not a bug). Android's `google-play-scraper` deep-paginates; iOS's RSS feed cannot. So iOS
> can only ever be a **current snapshot** across whichever markets are high-volume enough that
> 500 `mostrecent` reviews still land inside the last few weeks.

**Steps:**
1. **`scout_ios.py`** — probes a broad candidate set of 25 countries and keeps only those
   where 500 `mostrecent` reviews fall within ~21 days **and** are ≥50% English (`QUALIFY_DAYS`,
   `MIN_ENGLISH_PCT`). Result → `data/interim/ios_country_scout.json`.
   - **Qualifiers found:** **US (3d), GB (12d), CA (13d), IN (17d), AU (18d).** High-volume
     non-English markets (MX/BR/DE/FR/JP) were recent but failed English; low-volume English
     markets (NZ 208d, SG 186d, PK 381d) failed recency. Locked into `common.config.IOS_COUNTRIES`.
2. **`collect_ios.py`** — pulls `mostrecent` only across the 5 qualifying countries
   (`config.IOS_COUNTRIES`). `mosthelpful` was deliberately **dropped**: it spans ~8 years and
   skews the star mix (34% vs 64% 5★), which would corrupt the "current snapshot" framing.
   - **Outputs:** `data/raw/ios_raw.jsonl` (2,500), `data/raw/ios_manifest.json` (per-country span).

**Tests run:**
- Scraper validated on small runs before the full pull.
- EC-1 date-span probe (iOS hard cap at 500 ≈ 2–3 weeks) — drove the two-track split.
- The scout itself is the data-driven country-selection test (above).

**Result:** iOS 2,500 raw across US/GB/CA/IN/AU, all ≤18 days old.

**Exit criteria:** ✅ complete — 2,500 collected, manifest reconciles per-country counts.

**Checkpoints / human input:** none (scope locked with the user).

**How to re-run:**
```bash
./.venv/Scripts/python.exe -m ios.phase-1-collection.scout_ios        # refresh iOS country set
./.venv/Scripts/python.exe -m ios.phase-1-collection.collect_ios
```

> Note: these two scripts were originally under `phases/phase-1-collection/` (alongside
> `collect_android.py`); moved here because they are iOS-exclusive and have no code shared with
> the Android collector — nothing else in the repo imports them.
