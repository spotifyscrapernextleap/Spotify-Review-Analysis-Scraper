# Edge Cases & Failure Modes — Spotify Review Intelligence

How this project could fail, and how each failure will be **detected and invalidated during the build** rather than discovered at the end. Grouped by phase. IDs (EC-n) are referenced from each phase README's "Tests run" line.

**Severity:** 🔴 breaks a headline claim / the build · 🟠 distorts a number · 🟡 cosmetic / degraded.

---

## Collection (Phase 1)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-1 🔴 | **iOS only exposes a recent rolling window** — can't reach back months. | Would silently bias any iOS time-series / window. | **RESOLVED via two-track design:** measured iOS hard cap (500/country ≈ 2–3 wks) → iOS is built as a **current snapshot** (no trend/window); only Android (which deep-paginates) carries the 6-month temporal analysis. |
| EC-2 🔴 | **Store rate-limits / blocks the scraper** mid-run. | Partial corpus; biased toward whatever was pulled before the block. | Polite pacing + resumable checkpoints; on 4xx/5xx, back off and resume — never silently truncate. Manifest flags any country pulled incompletely. |
| EC-3 🟠 | **Pagination caps** (e.g. iOS RSS ~500/country/sort) yield too few reviews to reach saturation. | Can't reach thematic saturation; thin per-category bases downstream. | We **deliberately over-collect** (scrape many multiples of the substantive target across all countries/sort orders) precisely so caps don't starve us. ~2,000 is a saturation *reference, not a cap or gate* — we never stop because we hit it, and never trim substantive reviews down to it. The only gate is the *lower* one: if projected substantive volume (raw × survival rate) or emerging-theme saturation is too thin, widen collection before Phase 4/5. |
| EC-4 🟠 | **"Most-helpful" / "most-recent" sort bias** in what the store returns. | Sample not representative → invalidates absolute sentiment. | This is exactly what the **sampling-fairness eval (EC-19)** measures: collected vs store-reported star distribution. Bias reported as a number, and analysis leans on *within-pool gaps* (effect size), not absolute levels. |
| EC-5 🟡 | **Date/timezone/locale parse failures** on raw records. | Window assignment wrong; trend chart distorted. | Field-integrity check (EC-9): out-of-range/unparseable dates quarantined + counted, never coerced. |

## Filtering & tiering (Phase 2)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-6 🔴 | **Substance gate too strict** → kills short-but-substantive ("shuffle isn't random, repeats songs"). | Drops real Discovery signal; understates the headline problem. | Golden set includes short-but-substantive exemplars; gate must KEEP them. Unit test asserts golden-set verdicts; tune until pass. Final A/B-vs-C rides on Layer-1 category (a categorised review is substantive by definition). |
| EC-7 🟠 | **Substance gate too loose** → long-but-empty reviews pass. | Inflates substantive denominator; dilutes themes. | Golden set includes long-but-empty exemplars that must be DROPPED/Tier-C; same unit test. |
| EC-8 🟠 | **English filter false-drop (slang/emoji) / false-keep (Hinglish)**. | Violates the English-only claim both ways; loses Indian-market signal. | Language spot-check on a hand-labeled sample → measured false-drop / false-keep rates surfaced in the eval layer (EC-22), with a worked code-switched example. Reported as a known limit, not asserted clean. |
| EC-9 🔴 | **Malformed record coerced** (missing rating → 0). | Silently drags the star baseline down; corrupts the least-biased signal. | Field-integrity validation quarantines + **counts** bad records; unit test asserts no coercion-to-zero path exists. Surfaced as `evaluation.fieldIntegrity`. |
| EC-10 🟠 | **Near-dupe threshold mis-tuned** — over-merges distinct reviews or misses cross-country copies. | Wrong `deduplicated` count → wrong denominators. | Inspect a sample of merged/near-miss pairs; tune similarity threshold; funnel reconciliation (EC-20) proves removed counts add up. |

## Window derivation (Phase 3)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-11 🟠 | **Chosen window too thin** to reach saturation, or dominated by one app release. | Themes unstable; window justification indefensible. | Require the window to span ≥3–4 update cycles AND clear a minimum substantive-volume floor; if neither holds, widen. Justification written with the volume exhibit as evidence. |

## Layer 1 — broad categorisation (Phase 4)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-12 🔴 | **Groq free-tier limits hit mid-run** (tokens/RPM/daily cap). | Partial classification; budget claim false. | Calibrate tokens/latency on a tiny sample, verify live caps on the Groq dashboard **before** the full run (🔑 checkpoint); batch + cache the prefix; checkpoint progress so a cap-hit resumes, not restarts. |
| EC-13 🔴 | **Model returns invalid / off-schema JSON** (bad category id, missing field). | Pipeline crash or silent mis-labeling. | Per-item schema validation; one bounded repair retry; persistent failures → explicit abstain, never a guessed label. Count of repairs/abstains logged. |
| EC-14 🟠 | **Batch contamination / position bias** — labels bleed across items in a batch. | Systematic mislabeling invisible in aggregate. | Small A/B: same reviews, different batch positions/sizes → labels must be stable. Deferred deep check noted; spot-check run here. |
| EC-15 🟡 | **`other` overflows** — too many substantive reviews fit no category. | Signals a taxonomy gap; weakens share-of-voice. | Monitor `other` share; if large, inspect and decide whether a category is missing — but keep the six fixed per contract; document the call. |

## Layer 2 — deep Discovery coding (Phase 5)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-16 🔴 | **Evidence-snippet hallucination** — snippet not actually in the review. | Destroys the "receipts" credibility of the Evidence Explorer. | Automated assertion: every snippet must be a **verbatim substring** of its source review (normalised). Non-substring → reject + re-tag or abstain. |
| EC-17 🔴 | **Codebook doesn't fit the contract shape** — sub-themes don't map to `finding`/`recs` + `emerging`, or repetition cluster undefined. | Dashboard buckets/bridge can't render. | Consolidation step validated against `contract.py`: every theme has a `group`; every theme id referenced by `buckets` exists in `discovery.themes`; bridge totals reconcile. |
| EC-18 🟠 | **Too few Discovery reviews to deep-code** meaningfully. | Sub-theme counts become noise. | Gate: if `discoveryAll` below floor, widen collection (loop to EC-3) before coding. Thin sub-themes flagged, not presented with false confidence. |

## Gold set & validation (Phase 6)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-19 🔴 | **Circular validation** — same model labels the gold set it's graded against. | Accuracy number is meaningless. | Resolved by decision: **user hand-labels** the gold set, independent of the classifier (🏷️ checkpoint). Build enforces labels come from the user sheet, not the pipeline. |
| EC-20 🟠 | **Thin per-category base** (~8 each) makes per-category accuracy noisy. | Over-claimed precision on Discovery accuracy. | Report per-category as **directional**; flag any thin cell; grow the set if build has room. Kappa reported alongside raw rate to chance-correct. |
| EC-21 🟡 | **Gold set flattered by easy cases.** | Accuracy looks better than reality. | Composition is **deliberately borderline-weighted** and shown (borderline-vs-easy split) so the number isn't taken at face value. |

## Analysis & contract (Phase 7)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-22 🔴 | **Funnel leaks** — counts don't reconcile (in ≠ out + removed). | A funnel that leaks is a denominator that lies. | Automated reconciliation assertion at every step; surfaced as `evaluation.funnelReconcile`. Build fails if any step doesn't balance. |
| EC-23 🟠 | **Effect-size CI includes zero** / is weak. | Headline number invites the "just noise?" challenge. | Bootstrap the CI; report it honestly. If it includes zero, say so and frame the gap as directional — do **not** hide or massage it. |
| EC-24 🟠 | **A percentage emitted without its `n`.** | Violates the project's golden rule. | `contract.py` validation + a lint that every `pct`/share field has a paired count; snapshot rejected otherwise. |
| EC-25 🟠 | **Denominator mislabeled** (share of *all* vs *substantive* vs *deep-coded* mixed up). | Numbers technically right, narratively wrong. | Each metric tagged with its denominator in code; cross-checked against the Methodology "denominators" card before emit. |

## Dashboard & deployment (Phases 8–9)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-26 🔴 | **Emitted JSON doesn't match the schema** the dashboard expects. | Dashboard breaks / renders blank. | Single source of truth: dashboard + pipeline both validate against `contract.py`/its JSON-schema export. CI check on the committed snapshot before deploy. |
| EC-27 🟠 | **Divide-by-zero / NaN bar widths** when a count is 0 or a theme array is empty. | Broken charts, blank bars. | Guard all normalisations; render explicit empty states (Evidence Explorer already specs one). Test with a zeroed/edge snapshot fixture. |
| EC-28 🟡 | **Low-n segments shown with false confidence.** | Misleads the reader. | UI flags `size < 20` as "directional, low n" per spec; verified against a low-n fixture. |
| EC-29 🟡 | **Vercel build fails / fonts (Sora) don't load / snapshot not committed.** | No shareable link, or degraded look. | Local prod build before deploy; snapshot committed and import-checked; Sora self-host fallback; smoke-test the live URL as a third party. |

## Cross-cutting

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-30 🟠 | **Real data contradicts the mock narrative** (e.g. discovery isn't 2nd-largest; trend isn't flat). | Tempting to steer results to match the prototype copy. | Treated as expected, not a failure. Copy is data-driven where it states numbers; narrative framing adapts to real findings. Honesty guardrail in `architecture.md` §5. |
| EC-31 🟡 | **Re-run yields different counts** (non-determinism). | Reproducibility claim weakened. | Pin model + temperature=0 where possible; commit the snapshot as the canonical artifact; document that live re-scrapes shift counts and why. |

## Two-track design (Android deep / iOS snapshot)

| ID | Edge case / failure mode | Why it breaks the project | Detection & invalidation during build |
|----|--------------------------|---------------------------|----------------------------------------|
| EC-32 🔴 | **iOS country recency drift** — a low-volume market's 500 reviews span months, polluting the "today" snapshot. | iOS snapshot silently mixes old + new; "current" claim false. | `scout_ios.py` keeps only countries where 500 reviews ≤ 21 days **and** ≥50% English. Result tested: US/GB/CA/IN/AU qualify; NZ/SG/PK (months) excluded. Re-run scout if re-targeting. |
| EC-33 🟠 | **Sort-mixing bias** — pooling `mosthelpful` (8-yr, star-skewed) into iOS prevalence. | Corrupts iOS star baseline + share-of-voice. | `mosthelpful` **dropped entirely** (measured: 34% vs 64% 5★, spans to 2017). iOS uses `mostrecent` only. |
| EC-34 🟠 | **Cross-platform false comparison** — reader compares Android (6mo) vs iOS (this week). | Apples-to-oranges; misleading. | Each snapshot labels its period loudly; tracks built + rendered independently; no blended cross-platform metric emitted. |
| EC-35 🟠 | **Android sampling invalidity** — sampling a recency-sorted slice isn't random. | Biased category prevalence. | **Census-scrape the full 6-month population** first, *then* sample from the complete month strata — the MD's own validity condition, now satisfiable because we hold the whole window (not a sorted subset). |
| EC-36 🟠 | **Sample-based counts presented as exact** (Android `discoveryAll`, prevalence). | Overstates precision; violates "% carries its n" honestly. | Android prevalence = projected estimate **with margin of error**; baseline/star/volume stay census (exact). Snapshot distinguishes sampled-n from census-n. iOS is all census. |
| EC-37 🟠 | **Android 6-month scrape is heavy** (~414k records, ~40 min). | Time/storage; partial pull risk. | Resumable paging + per-country status in manifest; safety cap; runs in background. Scope trimmed to 3 countries with the user to bound cost. |
