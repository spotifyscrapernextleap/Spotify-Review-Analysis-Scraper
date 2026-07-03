# Architecture & Build Plan — Spotify Review Intelligence

> **Status (2026-06-30):** Android track BUILT (Phases 0–8) AND carried through a **codebook v3 revision +
> full dashboard revamp**. v3 retired the `autoplay` and `safe` sub-themes (a blind borderline test scored
> them 0/6) and re-coded the whole 1,792-review discovery pool on `gpt-oss-120b` → 1,462 confirmed; all four
> dashboard sections were rebuilt to read v3 (real funnel, LLM sentiment in Evidence, a redesigned Discovery
> Deep Dive, and a pipeline-spine Methodology). This file is the **original plan**; for current state, real
> numbers, the v3 decisions (§4 D16–D19), and what changed during the build, read `PROJECT_MEMORY.md` first,
> then the per-phase `phases/*/README.md`. Remaining: rebuild `dist/`, git push, Phase 9 Vercel deploy, iOS track.
> **Spec source of truth:** everything in `build and design docs/` is binding. Reading order:
> `spotify_review_intelligence_brief_final.md` → `README.md` (Data Contract) → `dashboard-design-spec.md` → `eval-strategy-appendix.md`.
> Where a companion doc is more specific than the brief, the companion doc wins.

---

## 1. What we are building (requirement, in one place)

A tool that collects publicly available Spotify reviews (iOS App Store + Google Play, English, multiple country stores), filters them to genuine signal, classifies them in two LLM layers, computes a fixed set of metrics + quality evals, emits `window.REVIEW_DATA` JSON snapshot(s), and renders them in a high-fidelity 4-section dashboard deployed as a shareable link.

### Two independent tracks (forced by the data, locked with the user)
Spotify's review velocity means the public feeds expose very different depths, so the build splits into **two independently-developed tracks**, each emitting its own snapshot of the same schema:

| | **Android track** | **iOS track** |
|---|---|---|
| Feed depth | deep-paginates → real **6-month** window | RSS **hard-capped ~500/country ≈ 2–3 weeks** |
| Countries | US, GB, IN | US, GB, CA, IN, AU (scout-selected: recent + English) |
| Strategy | census local + **stratified LLM sample** (the sampling MD) | **census everything** (small enough; no sampling) |
| Sources | `Sort.NEWEST`, full population | `mostrecent` only (`mosthelpful` dropped — spans ~8yrs, skews stars) |
| Dashboard | full incl. **volume-over-time + window** | current **snapshot** (no trend/window; share-of-voice still works) |
| Answers | how big is discovery *over 6 months*, relative + trend | how iOS users behave *right now* |

A platform toggle is a *later* visualisation question; the two tracks are built independently. Comparability caveat: the two cover different time spans — never blend them into one cross-platform number.

**Narrative spine (non-negotiable):** size the problem → show it's not the whole story → go deep on discovery → let anyone check the evidence → show the work.

**The binding interface** is the `window.REVIEW_DATA` schema in `README.md`. The pipeline's last job is to emit *exactly* that shape; the dashboard does display only, zero analysis. **Every percentage travels with its raw `n`.**

### Success criteria ("Done")
- Dashboard opens by sizing the problem (Overview), goes deep with evidence (Discovery Deep Dive + Evidence Explorer), and exposes methodology + a 7-visual evaluation layer.
- Automated categorisation has a **measured** accuracy against a user-labeled 50-review gold set (overall + per-category + kappa).
- Every prevalence figure has a stated denominator; effect-size gap shown against the star baseline with a CI.
- Pipeline runs within the Groq free-tier budget, confirmed against the live usage dashboard.
- Shareable link + documented, re-runnable repo.
- Limitations stated plainly, not hidden. **Real data is reported honestly even where it contradicts the mock's narrative.**

### Settled environmental decisions (2026-06-23)
| Decision | Choice |
|---|---|
| LLM provider | Groq free tier — `gpt-oss-120b` (deep Layer 2), `llama-3.1-8b-instant` (broad Layer 1). Key not yet provisioned. |
| Gold set | **User hand-labels** the 50 reviews; labels must not come from the classifier model. |
| Dashboard stack | React + Vite + Recharts (static SPA). |
| Pipeline stack | Python. |
| Deployment | Vercel (live shareable link + documented repo). |

---

## 2. Repository & phase conventions (binding rules for the build)

Two rules govern how work is organised, applied to **every** phase:

1. **One folder per phase.** All work produced for a phase — code, prompts, intermediate data, outputs, notes — lives inside that phase's folder under `phases/`, so each phase is self-contained and trackable in the repo history.
2. **One README per phase.** Every phase folder contains a `README.md` written from the template below, so anyone can understand what that phase did, what it produced, and how to re-run it — without reading the code.

Cross-cutting code that genuinely must be shared (the contract models, config, logging, store-agnostic helpers) lives in a small `common/` package and is *imported* by phases rather than copy-pasted — duplication is the only exception to "everything in the phase folder."

### Planned layout
```
spotify-review-intelligence/
├─ architecture.md                  ← this file
├─ edge-cases.md                    ← failure-mode chart
├─ README.md                        ← top-level repo readme (built in Phase 9)
├─ build and design docs/           ← binding specs (already present)
├─ common/                          ← shared, cross-phase code
│   ├─ config.py                    ← countries, app ids, window params, thresholds
│   ├─ contract.py                  ← pydantic models = window.REVIEW_DATA schema (validatable)
│   └─ io.py, logging.py
├─ data/                            ← raw scrape (gitignored if large); committed snapshot
└─ phases/
    ├─ phase-0-foundations/
    ├─ phase-1-collection/
    ├─ phase-2-filtering/
    ├─ phase-3-window/
    ├─ phase-4-layer1-broad/
    ├─ phase-5-layer2-discovery/
    ├─ phase-6-gold-validation/
    ├─ phase-7-analysis-snapshot/
    ├─ phase-8-dashboard/
    └─ phase-9-deploy-docs/
```

### Per-phase README template
```
# Phase N — <name>
**Objective:** one line.
**Inputs:** what it consumes (and from which prior phase).
**Steps:** the ordered work done.
**Outputs / artifacts:** files produced, with paths.
**Contract fields produced:** which window.REVIEW_DATA fields this phase fills.
**Tests run:** the checks that proved it works (see edge-cases.md IDs).
**Exit criteria:** what had to be true to move on.
**Checkpoints / human input:** any pause for the user (Groq key, gold labels).
**How to re-run:** exact command(s).
```

---

## 3. Phase-by-phase breakdown

Dependency order is linear with two reconciliation loops (tiering reconciles after Phase 4; window feeds analysis in Phase 7). Two **human checkpoints** are marked 🔑 (Groq key) and 🏷️ (gold-set labeling).

### Phase 0 — Foundations & scaffolding
- **Goal:** make the repo runnable and make the contract *enforceable* before any data exists.
- **Steps:** create layout + `common/`; pin Python deps; `.env` handling for `GROQ_API_KEY` (never committed); structured logging; encode the **`window.REVIEW_DATA` schema as pydantic models** so any emitted snapshot can be validated programmatically; author the **golden filter set** (≈20–30 worked examples: clear keep / clear junk / borderline short-but-substantive / long-but-empty) used to tune & test Phase 2; central `config.py` (countries US/UK/CA/AU/IN, app ids, ~12-month net, thresholds).
- **Outputs:** scaffolding, `contract.py`, `golden_set.jsonl`, config.
- **Exit:** a hand-written mock snapshot validates against `contract.py`; `golden_set` loads.

### Phase 1 — Collection (Stage 1)
- **Goal:** gather a **generous, deliberately over-collected** raw haul across the full ~12-month net and all country stores — so that substantive volume is driven by thematic saturation, not by a target number.
- **Sizing principle (important):** **~2,000 substantive is a saturation-informed reference, not a cap or a gate.** We scrape *much* more than 2,000 raw (several multiples), because the majority will not survive filtering, and because if the ideation/open-coding pass keeps surfacing new themes or new review types, we want headroom to go further. We never stop collecting *because* we hit 2,000, and we never throw away substantive reviews to get *down* to 2,000. The number that gets analysed is whatever the data supports once new reviews stop producing new themes.
- **Steps:** iOS scraper (App Store RSS / store API per country) + Android scraper (`google-play-scraper`); pull as much as each store reasonably allows across every country and sort order; rate-limited & resumable; capture raw fields + provenance (store, country, fetch time); store raw to `data/raw/`; record per-store/per-country pull counts.
- **Outputs:** raw review corpus + a collection manifest (counts by store × country × month).
- **Contract fields seeded:** `funnel.collected`, `platforms.*.count` (pre-filter).
- **Exit:** raw corpus is as large as the stores reasonably yield (well above what's needed for ~2,000 substantive, with headroom); manifest reconciles with stored records. The substantive count itself is *not* an exit gate here — it emerges after filtering + saturation.

### Phase 2 — Normalisation & filtering / guardrails (Stage 2)
- **Goal:** deterministic cleaning into Tier A/B/C — route, never delete.
- **Steps:** exact + near-dupe removal (cross-country); English language filter; junk rules (emoji-only, char-repeat, single-word, spam); field integrity (valid date, 1–5 rating, country, text-or-empty flag) with **quarantine + count, never coerce**; obvious contentless → **Tier C** (star retained). *Note:* the A/B-vs-C split for borderline reviews **rides on Layer-1 categorisation** (Phase 4) and is reconciled there — Phase 2 emits a "candidate substantive" set + a confident-Tier-C set. Tuned and unit-tested against the golden set.
- **Outputs:** tiered corpus, dedupe/junk logs, field-integrity report.
- **Contract fields seeded:** `funnel.deduplicated/english/tierC`, `evaluation.funnelReconcile` (collection rows), `evaluation.fieldIntegrity`, `evaluation.languageCheck`.
- **Exit:** funnel reconciles (in = out + removed) at every deterministic step; golden-set filter tests pass.

### Phase 3 — Window / volume-over-time (Android track only)
- **Goal:** build the temporal backbone from the Android 6-month census.
- **Steps:** plot review volume + avg rating by month over the 6-month census (census = exact counts, no sampling); confirm it spans several update cycles; write the justification; produce the volume-over-time exhibit + monthly strata for the LLM sample.
- **Outputs:** monthly volume/rating table + chart, window justification, month strata.
- **Contract fields produced (Android snapshot):** `window.*`, `trends`, `trendDirection`.
- **iOS:** N/A — iOS is a ~2–3 week snapshot; its snapshot sets `window` to a "current snapshot" note and **omits `trends`/`trendDirection`** in the dashboard view (cross-sectional share-of-voice is still shown).
- **Exit:** Android volume-over-time computed across the 6-month census; iOS snapshot framed as current.

### Phase 4 — Categorisation Layer 1: broad pass (Stage 3) 🔑
- **Goal:** file substantive reviews into 6 categories (+`other`) with sentiment — the cheap, high-volume pass.
- **Per track:** **Android** classifies a **stratified month sample** (~2k/month, volume-weighted for headline numbers — the sampling MD); **iOS** classifies **everything** (~2.1k, small enough — census). Both use one taxonomy.
- **Steps:** **small calibration run first** to measure tokens/latency, then **pause for `GROQ_API_KEY` + verify live limits on the Groq usage dashboard** before the full run; `llama-3.1-8b-instant`; batched calls; cached instruction+codebook prefix; strict JSON output validated per item (reject/repair off-schema); abstention allowed; per-run token accounting. **Reconcile final Tier A/B vs C** here (a review that earns no category → Tier C).
- **Contract note:** for Android, category prevalence + `discoveryAll` are **sample-based estimates** projected to the census with a margin of error; for iOS they are exact (census). Baseline/star/volume are census (exact) on both. Every share still travels with its (sampled or census) `n`.
- **Outputs:** category+sentiment labels, token-accounting log, reconciled tiers (per track).
- **Contract fields produced:** `categories`, `funnel.tierA/tierB/substantive/discoveryAll`, `baseline` inputs, `delight`, `sentimentSplit`.
- **Exit:** sampled/census reviews labeled or explicitly abstained; tiers reconcile; run within budget.

### Phase 5 — Categorisation Layer 2: deep Discovery coding (Stage 3)
> **As built (v3):** the codebook went v1→v2→v3. v3 RETIRED `autoplay` + `safe` (borderline test scored them
> 0/6) and the full 1,792-review pool was re-coded on `gpt-oss-120b` with 3 guardrails → 1,462 confirmed. See
> `phase-5-layer2-discovery/codebook_v3_REVISED.md`, `recode_v3.py`, `borderline_test.py`, and PROJECT_MEMORY D16.
- **Goal:** the differentiated work — open-code → codebook → closed-code Discovery reviews.
- **Steps:** open pass on a small Discovery sample (themes surface freely); **human consolidation into a fixed codebook** shaped to the contract (each sub-theme has a `group` ∈ repetition|relevance|features|positive; maps into `finding`/`recs` buckets + `emerging`; repetition cluster identified; chosen-vs-imposed split for the bridge); closed classification at scale on `gpt-oss-120b` with **evidence snippets**, abstention, and the `emerging` escape hatch; extract implied use-case tags.
- **Outputs:** codebook doc, deep-coded discovery records with snippets, theme/bucket/bridge tables.
- **Contract fields produced:** `discovery.*`, `buckets`, `bridge`, `behaviors`, `unmetNeeds`, `segments`, `quotes`, `positiveDiscoveryThemes`, `funnel.deepCoded`, `evaluation.abstention`.
- **Exit:** every snippet is a verbatim substring of its source review; sub-themes map cleanly to the contract shape; `emerging` populated rather than force-fitting. **Saturation check:** if the open-coding sample is still surfacing genuinely new themes, widen the sample / pull more reviews (loop back to Phase 1) rather than freezing the codebook early — saturation, not a count, decides when coding is "enough".

### Phase 6 — Gold set & validation 🏷️
- **Goal:** measure classification quality, don't assume it.
- **Steps:** assemble a 50-review gold set **deliberately weighted toward borderline cases** and covering all six categories (≥7–8 each); generate a labeling sheet; **pause for the user to hand-label** (labels independent of the classifier); compute overall accuracy, per-category accuracy, **kappa**, confusion matrix, gold-set composition, abstention calibration; flag thin per-category cells rather than over-claiming.
- **Outputs:** labeling sheet, user labels, validation metrics.
- **Contract fields produced:** `validation`, `evaluation.confusion`, `evaluation.goldComposition`, refines `evaluation.abstention`.
- **Exit:** metrics computed from user labels; thin cells flagged; numbers reported as-is.

### Phase 7 — Analysis, metrics & snapshot emission (Stage 4)
- **Goal:** compute every number the dashboard shows and emit the validated snapshot.
- **Steps:** share of voice (with denominators), star baseline, **effect size + CI (bootstrap)**, trends + direction read-out, repetition cluster, chosen/imposed bridge totals, unmet needs, segments (flag size<20), delight, sentiment split; complete the collection-layer evals (sampling fairness vs store-reported distribution, funnel reconciliation, field integrity, language spot-check); **assemble `window.REVIEW_DATA` and validate it against `contract.py`**.
- **Outputs:** `REVIEW_DATA.json` (committed snapshot), analysis notebooks/scripts.
- **Contract fields produced:** `effect`, `trendDirection`, `evaluation.sampling`, `limitations`, and final assembly of all fields.
- **Exit:** snapshot passes schema validation; every `pct` has its `n`; funnel reconciles end-to-end; CI computed (reported honestly whether or not it excludes zero).

### Phase 8 — Dashboard (Stage 5)
> **As built (revamped):** all four sections were rebuilt beyond the prototype — Overview shows the REAL funnel
> + a "Category Sentiment" panel; Evidence uses LLM sentiment (pos/neg/mixed) + "also:" co-tag chips; Discovery
> Deep Dive is a redesigned funnel/bucket layout on v3 data with the counterweight moved in; Methodology is a
> "pipeline spine" (8 stages, What/Why/How-checked, only the checks that worked). See PROJECT_MEMORY D17–D19.
- **Goal:** recreate the prototype in React + Vite + Recharts, reading the snapshot.
- **Steps:** scaffold Vite app; load `REVIEW_DATA` once (single source); implement the 4 sections (Overview, Discovery Deep Dive, Evidence Explorer, Methodology & Evaluation) to the design tokens (Sora, color/spacing/radius); state per README (`activeSection`, `evalOpen`, `selectedTheme`, `evSentiment/Platform/Country`); real charts (Recharts) for trend line, histograms, confusion-matrix heatmap, diverging bars; the inline-expanding eval layer; empty/low-n states; **no crosswalk tab** (only the quiet `↳ addresses Q…` tags).
- **Outputs:** working dashboard app.
- **Exit:** renders the real snapshot with no schema edits; matches the prototype's look; all interactions work; degrades gracefully on empty/low-n.

### Phase 9 — Deployment & documentation
- **Goal:** ship the shareable link + a re-runnable repo.
- **Steps:** Vercel config + deploy reading the committed snapshot; top-level repo `README.md` (run the pipeline, re-run with a different app/window/taxonomy, parameterisation); final QA pass against "Done"; provenance footer replacing "Prototype · Mock Data".
- **Outputs:** live URL, repo docs.
- **Exit:** link opens for a third party; pipeline documented well enough to re-run.

---

## 4. Dependency graph & checkpoints

```
P0 ─► P1 ─► P2 ─► P3 ─► P4 🔑 ─► P5 ─► P6 🏷️ ─► P7 ─► P8 ─► P9
                   │            ▲                  ▲
                   └─ window ───┘ tier reconcile   │
                   └──────────── feeds analysis ───┘
```
- 🔑 **Groq key checkpoint** (start of Phase 4): calibrate on a tiny sample, then pause for the key + verify live limits before the full classification run. Phases 0–3 need no key.
- 🏷️ **Gold-labeling checkpoint** (Phase 6): pause for the user to label the 50-review set before any accuracy/kappa/confusion number is computed.

## 5. Honesty & reproducibility guardrails (carried across all phases)
- The mock numbers are fabricated; the real scrape will differ. Report what the data says; do not steer results toward the mock narrative.
- Nothing is deleted, only routed; the right denominator is chosen per question and always stated.
- The pipeline is parameterised (app, countries, window, taxonomy) so the tool is reusable, not a one-off.
- Each phase's README records exactly how to re-run it.
