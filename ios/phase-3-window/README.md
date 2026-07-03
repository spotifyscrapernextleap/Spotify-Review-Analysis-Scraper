# Phase 3 — Window / Volume-over-time — N/A for iOS

**Status:** intentionally skipped for this track.

**Why:** Phase 3 builds the temporal backbone (monthly volume, monthly avg rating, app-version
cycle count) from a multi-month census. iOS has no such census — the iTunes RSS feed
hard-caps at ~500 reviews/country ≈ 2–3 weeks (see `ios/phase-1-collection/README.md`), so
there is no time dimension to bucket. iOS is reported as a **current snapshot**: the dashboard
shows a "current snapshot, no trend" note instead of a trend chart, and the iOS contract
`window` field carries a short justification string rather than monthly `trends`.

See `phases/phase-3-window/README.md` for the Android-only window derivation this phase
produces (Dec 2025 – Jun 2026, 7 calendar months, 21 app-version cycles).

**No script lives in this folder** — there is nothing for iOS to compute here.
