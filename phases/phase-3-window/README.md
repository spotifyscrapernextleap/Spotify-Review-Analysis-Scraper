# Phase 3 — Window / Volume-over-time (Android track only)

**Objective:** build the temporal backbone from the Android 6-month census — the exhibit that lets the dashboard show discovery *over time*, and the strata the LLM sample draws from.

**Why Android only:** iOS is a ~2–3 week snapshot (store feed cap), so it has no time series. iOS reports `window` as a "current snapshot" note and omits the trend chart. Only Android deep-paginates far enough for a real window.

**Inputs:** `data/interim/android/{substantive_candidates,tierC}.jsonl` (all English Android reviews = the census baseline population).

**Steps:** bucket every English review by calendar month → monthly volume + monthly avg star rating (census, exact); count distinct `major.minor` app-version cycles spanned; emit the window string + justification + monthly strata counts (sampling frame for Phase 4). The discovery-share overlay on the trend (`discoveryPct`) is left null here — it needs Layer-1 categorisation (filled post-Phase-4).

**Outputs:** `data/interim/android_window.json` (window, trends skeleton, strata_counts).

**Contract fields produced (Android snapshot):** `window.*`, `trends` (volume + avgRating; discoveryPct pending), feeds `trendDirection`.

**Result:**
- **Window: Dec 2025 – Jun 2026** (7 calendar months; Dec & Jun are partial at the cutoff boundaries), spanning **21 distinct app-version cycles**.
- Monthly volume / avg rating (census, exact):

| Month | Reviews | Avg ★ |
|---|---|---|
| Dec 2025 | 5,345 | 3.91 |
| Jan 2026 | 20,797 | 3.95 |
| Feb 2026 | 17,831 | 3.82 |
| Mar 2026 | 20,579 | 3.65 |
| Apr 2026 | 19,545 | 3.89 |
| May 2026 | 23,205 | 3.67 |
| Jun 2026 | 17,295 | 3.66 |

(Avg rating drifts slightly down across the window, 3.95 → 3.66 — a real signal to revisit once categories are attached.)

**Exit criteria:** ✅ 6-month census window computed; volume + rating per month exact; strata ready for sampling; 21 update cycles documents the window spans many releases (no single release dominates).

**How to re-run:**
```bash
./.venv/Scripts/python.exe -m phases.phase-3-window.derive_window
```
