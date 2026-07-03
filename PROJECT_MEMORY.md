# PROJECT_MEMORY.md — Context Handoff

> Audience: a competent engineer with zero prior context. This captures the **non-obvious**
> reasoning, history, and gotchas. For things already documented in depth, this points to the
> file rather than repeating it (see footer).
>
> **State as of this handoff (2026-06-30): ANDROID track built (Phases 0–8) AND through a v3 revision +
> full dashboard revamp.** Android Layer-1 done (23,508 sample, v5 multi-label); discovery deep-coded; then a
> **codebook v3** pass — `autoplay` and `safe` REMOVED after a blind borderline test scored them 0/6, and the
> ENTIRE 1,792-review discovery pool was re-coded on **gpt-oss-120b** with strict guardrails → **1,462
> confirmed discovery** (330 dropped: 327 not-discovery, 3 non-English). The dashboard now reads v3 end-to-end
> and all four sections were revamped (see §4 D16–D19). `data/REVIEW_DATA.android.json` emitted + contract-valid.
> **Still TODO:** (a) **rebuild `dist/`** (held during iteration); (b) **git init + push** (see §7 — verify
> `.env`/`node_modules`/`dist`/`data/raw` are gitignored FIRST); (c) **Phase 9 Vercel deploy** (user handles
> auth); (d) the **iOS track** — now scaffolded under a new top-level `ios/` folder mirroring `phases/`
> (see D20, §7 item 4). Phases 1–2 done (2,106 candidates); Layer-1 census, recall-recovery, Phase 5
> v3 deep-coding, a ~25-review gold sheet 🏷️, and Phase 7 snapshot remain, ending at
> `data/REVIEW_DATA.ios.json` — dashboard wiring is a later, separate effort.

---

## 1. PROJECT OVERVIEW

A pipeline that scrapes public **Spotify app-store reviews** (Apple App Store + Google Play),
filters them to genuine signal, classifies them with two LLM passes, and (eventually) emits a
single JSON snapshot that drives a static dashboard. It's an assignment-style **review-intelligence**
tool: the headline question the brief poses is "how big is the *music-discovery* problem relative to
everything else, and what exactly are users complaining about?"

The deliverable is a shareable dashboard backed by a documented, re-runnable repo. The conceptual
"source of truth" is `build and design docs/spotify_review_intelligence_brief_final.md`.

**TWO most important real-world findings (both contradict the mock; we report honestly):**

1. **Discovery is NOT the dominant problem.** Android Layer-1 (v5, 13,248 codeable, multi-label so shares
   sum >100%): **pricing/ads 52.8%** (#1), tech 18.7%, **discovery 17.8%** (clear 2nd tier), ux 11.8%,
   updates 6.2%, catalogue 5.0%, audio 4.2%, other 1.0%. Effect size (Phase 7, census baseline + bootstrap):
   discovery **3.35★ vs 3.78★ baseline = −0.43 (95% CI [−0.50, −0.36])** — real but far smaller than the
   mock's −0.8; discovery is below baseline yet *less* negative than the average complaint (codeable avg 2.65).

2. **Within discovery, the problem is LOSS OF CONTROL, not "bad recommendations."** Reshaped the codebook
   across v1→v2→v3. **Current (v3, gpt-oss-120b, 1,462 confirmed discovery):** `control` **26.9%** (#1 — loss of
   control over playback), `love` 23.6% (positive), `repeat` 12.7%, `shuffle` 11.5%, `freegate` 10.5%,
   `mismatch` 7.7%, `smartrec` 3.2%, `pushy` 2.9%, `dj` 2.3%, `newmusic` 2.0%. v3 makes "loss of control" the
   unambiguous #1 (v2 had it 2nd behind an inflated `love`; the strict gate deflated generic praise). The
   repetition cluster (`repeat`+`shuffle`) is **315 imposed : 1 chosen** — overwhelmingly app-imposed, so the
   bridge is reframed imposed-dominant. NOTE: v3 RETIRED `autoplay` (folded into `control`) and `safe` (folded
   into `repeat`), and `pushy` collapsed from a v2-inflated 17% to 2.9% (120B correctly split "invades my
   playlist"→control vs "pushes AI slop at me"→pushy). The broad-category Layer-1 numbers in finding #1 are
   UNCHANGED by v3 (v3 only re-coded discovery sub-themes).

---

## 2. ARCHITECTURE

There is **no server, no database, no auth, no live backend.** It is a batch pipeline writing files,
plus a (not-yet-built) static dashboard. "Architecture" here means data flow through phases.

### In words
- **Collection (Python)** → store scrapers write raw JSONL to `data/raw/`.
- **Filtering (Python)** → deterministic guardrails write tiered JSONL to `data/interim/{track}/`.
- **Classification (Python + Groq API)** → two LLM passes label reviews.
- **Analysis (Python, not built)** → computes every number and emits `window.REVIEW_DATA` JSON.
- **Dashboard (React, not built)** → reads that JSON snapshot, display-only.
- **External service:** Groq (LLM inference, free tier). That's the only external dependency.

### TWO INDEPENDENT TRACKS (the defining architectural decision — see §4)
Android and iOS are built as **separate pipelines producing separate snapshots of the same schema**,
because the two store feeds expose fundamentally different depth:
- **Android track:** US/GB/IN, deep-scraped **6 months**, census + LLM **sample**. Full temporal dashboard.
- **iOS track:** US/GB/CA/IN/AU, `mostrecent` only (~2–3 week snapshot), **census** (classify all). No trend/window.

### Tech stack & WHY
- **Python 3.9.9**, venv at `.venv/` (run things as `./.venv/Scripts/python.exe -m phases.<pkg>.<mod>`). Windows host.
- **`google-play-scraper`** — Android reviews; it deep-paginates (essential for the 6-month window).
- **iTunes RSS customer-reviews feed via `urllib`** for iOS — **NOT `app-store-scraper`**: that package's
  Apple endpoint is broken (returns non-JSON / "Expecting value"). RSS is reliable but hard-capped (see §5).
- **`pydantic` v2** — encodes the binding data contract (`common/contract.py`) so any emitted snapshot is validatable.
- **`langdetect`** — English filter, with a Latin-script + English-token fallback to keep Hinglish/slang.
- **`groq`** SDK — LLM calls. Free tier chosen per the brief (cost = 0).
- **`rapidfuzz`** is in `requirements.txt` but ended up **unused** — dedup is exact/id-based, not fuzzy (see §4/§5).
- **React + Vite + Recharts** (planned) for the dashboard — matches the HTML prototype, deploys as a static SPA.
- **Vercel** (planned) for hosting.

### Key directories
- `common/` — shared code: `config.py` (all parameters), `contract.py` (the schema), `io.py`, `logging_setup.py`.
- `phases/phase-N-name/` — one folder per pipeline phase for the **Android** track (plus the two
  track-parameterized phase-2/phase-4-broad scripts both tracks call), each with its own `README.md`.
- `ios/phase-N-name/` — the **iOS** track's mirror of the same phase-by-phase convention (see D20)
  — only for code that is genuinely iOS-exclusive; scripts already shared via a `track` arg stay in
  `phases/`. `ios/README.md` explains which is which per phase.
- `data/raw/` (gitignored), `data/interim/` — pipeline artifacts.
- `build and design docs/` — the binding specs (brief, data contract, dashboard spec, eval appendix).

---

## 3. DATA MODEL

File-based (JSONL), no DB. Key record shapes:

**Raw review** (`data/raw/{android,ios}_raw.jsonl`):
`review_id` (`"{store}:{country}:{store_id}"`), `store`, `country`, `rating` (1–5 int), `text`,
`title`, `date` (ISO), `app_version`, `thumbs_up`, `fetched_at`.

**Filtered/tiered** (`data/interim/{track}/substantive_candidates.jsonl`, `tierC.jsonl`, `quarantined.jsonl`):
adds `tier` (`AB_candidate` / `C`) and `tierC_reason`.

**Layer-1 output** (`data/interim/{track}_layer1.jsonl`) — **v5 multi-label schema**:
`review_id, store, country, rating, date, text, categories` (**list of 1–3**), `sentiment`
(`positive|negative|mixed`), `confidence` (`high|low`).

**The binding interface — `window.REVIEW_DATA`:** the JSON the dashboard consumes. Schema is defined
in code at `common/contract.py` (pydantic models + `cross_checks()`), mirrored from
`build and design docs/README.md`. Do **not** improvise its shape. `common/contract.py` also has
consistency checks (funnel reconciliation, bucket→theme id integrity, baseline sums).

**Taxonomy (v5):** `discovery, tech, ux, pricing, catalogue, audio, updates, other` (8 display
categories) + two routing-only labels: `none` (contentless → Tier C) and `podcast` (podcast-only →
**discarded**, out of scope). Defined in `common/config.CATEGORIES`.

Non-obvious constraints:
- **Android `country` is meaningless** and is overwritten to `"global"` during dedup (see §4/§5).
- **Multi-label means category shares can sum to >100%** (a review can raise 2–3 categories).
- **Android category counts are sampled estimates (± margin of error)**; iOS counts are census/exact.

### Funnel numbers (as collected)
- **Android:** 387,086 raw → **129,045 unique** (id-dedup) → 124,597 English → **96,822 substantive
  candidates** + 27,775 Tier C. LLM **sample = 23,538** (`android_layer1_sample.jsonl`, seed 42).
- **iOS:** 2,500 raw → 2,398 English → **2,106 substantive** + 292 Tier C (census-classified).

---

## 4. KEY DECISIONS & RATIONALE  *(most important section)*

**D1 — Two independent tracks (Android deep / iOS snapshot).**
Chose: separate pipelines + separate snapshots. Rejected: one unified pipeline; also rejected a heavy
~700k-record scrape to force a 6-month iOS window. Why: empirically, the iTunes RSS feed is **hard-capped
at ~500 reviews/country ≈ 2–3 weeks** for an app Spotify's size; it *cannot* go deeper. Google Play
*can* deep-paginate. Forcing symmetry would either fake iOS history or require an abusive scrape.
Trade-off: the two tracks cover different time spans and **must never be merged into one cross-platform
number**.

**D2 — Over-collect; saturation, not a 2,000 cap.**
The brief's "~2,000 substantive" is a **reference, not a gate**. We scrape far more and let thematic
saturation decide. (User was explicit about this.)

**D3 — Census what's free, sample what costs.**
Local steps (language, dedup, tiering, star/volume stats) run on the **full** population (exact counts).
The **LLM** steps run on a **sample** for Android (free-tier budget): stratified by month, **2,000–4,000
per month** scaled to that month's volume (floor 2k so quiet months aren't drowned, cap 4k so spike
months don't dominate; `phases/phase-4-layer1-broad/sample.py`). iOS is small enough to classify in full
(census). Why the 2k–4k scaling specifically: user wanted high-volume months not to "compete" with
low-volume ones. Consequence: **Android prevalence is an estimate ± MoE; iOS is exact.**

**D4 — Dedup by underlying reviewId, and Android `country` is not a real dimension.**
Discovered: `google-play-scraper`'s `country` param does **not** segment reviews — 129,012 of 129,045
reviewIds appeared in **all three** country pulls (it returns the same global stream). So the 387k raw
is ~3× duplication. We dedup by the underlying store reviewId (exact identity) **before** any text
dedup, and **relabel Android `country` → `"global"`**. iOS reviewIds *are* genuinely per-storefront
(0 cross-country dupes), so iOS country is real. This also matters for the **star baseline**: short
duplicated reviews ("good") must not be 3×-counted.

**D5 — Lenient deterministic filter; "substance rides on Layer-1."**
Phase 2 only catches *obvious* junk (emoji-only, single-word, char-repeat, spam, empty). Borderline
contentless praise ("Best music app ever!") is deliberately **passed through** as a candidate, and
Layer-1 routes it to `none` → Tier C. Why: the brief says a word-count substance gate is unreliable
(it would drop "shuffle isn't random" and keep long empty rambles). User explicitly chose "proceed as
is" on this. Verified against the golden set (see §6).

**D6 — Two LLM models, separate quotas.**
Layer-1 broad pass = `llama-3.1-8b-instant`. Layer-2 deep Discovery coding (not yet run) =
`openai/gpt-oss-120b`. Why two: their Groq rate limits are **independent pools**, so exhausting the 8B
budget does not block the 120B work. (`gpt-oss-120b` chosen over the deprecated `llama-3.3-70b-versatile`
the brief named.)

**D7 — Multi-key rotation across *separate accounts*.**
Groq rate limits are **per account/organization, not per API key** — multiple keys in one account share
one budget. So we use keys from **separate Groq accounts** (`GROQ_API_KEY`, `GROQ_API_KEY_2/3/4` in
`.env`), round-robined by `KeyPool` in `classify.py`, to multiply the daily token budget. A key that
returns a *daily* rate-limit error is dropped from rotation; the run is resumable so it continues when
budgets recover. (ToS caveat: multi-account free-tier use is a gray area; fine for an assignment, not
for production — a paid tier would be the clean path.)

**D8 — Multi-label classification (1–3 categories) + taxonomy changes.**
Moved from single-label to **1–3 labels/review**. Renamed `playback` → `tech`. **Added `updates`**
category. **Discard podcast-only** reviews (out of scope). All driven by the user's review of real data.

**D9 — Prompt v5, hardened from blind spot-checks (see §5 for the journey).**
The current prompt (`SYSTEM` in `classify.py`, `PROMPT_VERSION = "v5-multilabel-2026-06-25"`) encodes
hard rules learned from manual checks: **ads ALWAYS → pricing** (never tech/catalogue); **vague praise
→ `none`, not `other`**; smart-shuffle/autoplay → discovery; casting/account-errors → tech; `updates`
is additive (co-tag the real issue).

**D10 — Gold set is *user*-labeled (Phase 6, not done).** The 50-review validation set must be labeled
by a human independent of the classifier — otherwise accuracy is circular. (Distinct from the *golden
set*, see §5.)

**D11 — Window derived from data.** Android analysis window = the 6-month census it actually has
(Dec 2025–Jun 2026, ~21 app-version cycles; `phases/phase-3-window/derive_window.py`). iOS has no
window/trend — it's a current snapshot. `mosthelpful` iOS sort was **dropped** (it spans ~8 years and
skews the star mix; would corrupt a "current" snapshot).

**D12 — 8B over-tags discovery (safe), validated by a recall probe; recovered the misses.** Phase-5
prep found the 8B's `discovery` tag has ~38–44% **false positives** (over-tagging) BUT only **~3.6%
false negatives** (recall ~96%, measured by deep-coding 250 non-discovery reviews on 120B). Over-tag is
the safe error — the 120B deep pass filters the junk. The misses concentrated in `ux`/`updates`, so a
**census of those two piles** recovered **136** real discovery reviews, folded into the deep-code pool
(2,359 + 136 = 2,495). Scripts: `phases/phase-4-layer1-broad/recall_probe.py`, `recover_discovery.py`.

**D13 — Codebook v2 + a Claude hand-coded re-code for the discovery analysis.** Gold-set validation
showed the model's discovery sub-theme coding had fuzzy boundaries + a ~10% gap, so the codebook was
revised to **v2** (12 themes: added `smartrec` = constructive/feature rec requests; `dj`=problems-only;
explicit co-tag rules — free-tier-shuffle→shuffle+freegate, queue→autoplay+control, positive-feature→love;
up to 3 labels). **User ruled out re-running the open models** for this deadline pass (rate limits) and
insisted on **full-corpus correctness** ("the dashboard should work for us"), so **Claude hand-coded the
pool against v2**. The distribution **converged by 690/1,792** (stable across 90/390/690 checkpoints), so
we **locked at 690** as the corrected analysis basis; the 1,792 model-coded records stay the quote pool.
Canonical model for any FUTURE re-run is still **gpt-oss-120b**. Harness: `phases/phase-5-layer2-discovery/recode_claude.py`
(`build`/`dump`/`merge`); labels in `data/interim/phase5_recode_labels.jsonl`. `codebook_v2_REVISED.md`.

**D14 — Phase 7 = census-exact where free, sample-projected where it costs (consistent with D3).**
`build_snapshot.py` reports collection/dedup/English/star-baseline/monthly-volume as **census-exact**;
category/substantive/discovery counts are **stratified-sample estimates projected to the 96,822 population
± MoE** (stated in `limitations`). Effect size uses a **2,000-sample bootstrap CI**. Sampling-fairness
check passes by construction — Android was census-scraped (full NEWEST feed), so collected ≈ store dist.

**D15 — Dashboard is data-driven, and adapted where our reality differs from the mock.** The prototype
hard-codes some overview numbers (`17.5%`, `−0.8★`); the React port wires **every** value to the snapshot.
The confusion matrix is the **discovery sub-theme** matrix (the broad-category gold set is parked, unlabeled);
the Evidence country/platform chips derive from the actual quotes (Android / GLOBAL); the bridge renders the
honest ~0-chosen / imposed split.

**D16 — Codebook v3: removed `autoplay` + `safe`, full 120B re-code with strict guardrails.** A blind
borderline re-label (`phases/phase-5-layer2-discovery/borderline_test.py`; user hand-labeled 22 reviews from
the 4 fuzziest themes) found **`autoplay` and `safe` confirmed 0/6** — a human never kept those labels.
`codebook_v3_REVISED.md` retires both (autoplay→`control`, safe→`repeat`/`newmusic`/`mismatch`/`smartrec`),
leaving 10 themes. The ENTIRE 1,792-review pool was then re-coded on **gpt-oss-120b** (NOT Claude — user wanted
the canonical model) via `recode_v3.py`, with **three guardrails** so non-discovery never enters the inventory:
(1) deterministic langdetect drop before any model call, (2) a strict in-prompt discovery gate (precision over
recall), (3) `not_discovery` records excluded. Result: 1,462 confirmed / 330 dropped. Outputs:
`phase5_recode_v3_{coded,dropped}.jsonl` + `phase5_recode_v3_analysis.json`. Canonical re-run model stays 120B.

**D17 — Real funnel everywhere, not projected estimates.** User flagged the projected `substantive 54,564` /
`discovery 9,716` as confusing. The dashboard now shows the REAL pipeline (`387,086→124,597→96,822→23,508` and
the discovery sub-funnel `23,508→13,248→2,359→1,462`). `build_snapshot.py` exposes `funnel.substantiveCensus`
(96,822), `funnel.sampled` (23,508), `funnel.contentBearing` (13,248), `discovery.sampleN` (2,359),
`categories[].sampleCount` (actual sample n, not projected). The projected fields still exist for any code that
needs them; the UI just doesn't lead with them.

**D18 — Evidence Explorer: LLM sentiment + co-tags.** The Evidence quote chips were derived from a star
threshold (`rating>=3`). Now they carry the **Layer-1 LLM sentiment** (`positive|negative|mixed`, joined by
review_id) and an `otherThemes` list (the review's other v3 co-tags), shown as "also: <theme>" chips. Mixed is
a real third option the star threshold was hiding.

**D20 — iOS gets its own top-level `ios/` folder, mirroring `phases/`, but only for
code that is genuinely iOS-exclusive.** Chosen: a new `ios/phase-N-name/` tree with the same
Objective/Inputs/Steps/Outputs/Contract-fields/How-to-re-run README convention as `phases/`.
Rejected: forking copies of `filter_reviews.py` (Phase 2) and `classify.py` (Phase 4 broad)
into `ios/` — both are **single scripts parameterized by a `track` arg by design**, so both
tracks apply the identical deterministic filter rules and the identical hardened v5
classification prompt (D9). Forking them would risk the two tracks' category definitions
silently drifting apart over time — exactly the risk the user was checking for when asking
whether iOS Layer-1 would use the same tenets as Android's post-reclassification prompt. So:
`scout_ios.py`/`collect_ios.py` (already iOS-exclusive, zero Android coupling) **moved** to
`ios/phase-1-collection/`; `filter_reviews.py`/`classify.py` **stay** in `phases/`, invoked
with `track=ios`; everything genuinely new for iOS (Phase 4 recall-recovery, all of Phase 5
deep-coding, Phase 6 gold validation, Phase 7 snapshot) gets built fresh under
`ios/phase-N-name/`, referencing shared docs (e.g. `codebook_v3_REVISED.md`) rather than
copying them.

**D19 — Discovery + Methodology fully revamped.** Discovery Deep Dive ported a Claude-design mockup but with
REAL v3 data (4-card funnel, single sub-theme bar, finding/recs bucket cards with editorial summaries hardcoded
in `Discovery.jsx`, an honest NOTE replacing the too-thin segment data, the counterweight MOVED in from
Overview, imposed-dominant bridge). Overview lost the counterweight and renamed its sentiment panel to
**"Category Sentiment."** Methodology was rebuilt as a **PIPELINE SPINE**: 8 numbered stages
(Collect/Clean/Filter/Census-vs-sample/Broad/Deep-dive/Snapshot+contract/Limitations), each as
**What we did / Why we did it / How we checked** + one proof visual. Principle "show only what worked" dropped
the language-check + abstention charts and the hidden eval-layer expander. Stage 6 is the centrepiece: the
codebook v1→v2→v3 timeline + the 50-review gold confusion matrix (the diagnosis) + the borderline 0/6 test (the
action). The gold matrix keeps its v2 labels (incl. autoplay/safe) ON PURPOSE — it is the "before" picture that
motivated v3, not a stale artifact. New snapshot field: `methodology` (recallProbe/borderline/v3recode/codebook).

---

## 5. GOTCHAS & LANDMINES

Real bugs/surprises we hit (the "we already paid for this" list). Broader pre-identified failure modes
live in `edge-cases.md` (EC-1…EC-37).

- **OOM that lost an entire scrape.** The first Android collector accumulated all reviews in RAM and
  wrote only at the very end → the OS killed it at ~354k reviews and **everything was lost** (no
  incremental save, despite being called "resumable"). Fix: `collect_android.py` now **streams each
  country to disk page-by-page** (`data/raw/android/{cc}.jsonl`), writes a `{cc}.done.json` sidecar per
  finished country, keeps only counts in RAM, and skips completed countries on re-run. New dev landmine:
  don't "optimize" by buffering rows in a list.
- **Groq daily limit is a ROLLING 24h window, not a midnight reset.** Keys do not all free up at 00:00
  local or UTC; yesterday's heavy use keeps counting until ~24h after the peak. This repeatedly looked
  like "the keys didn't reset." ~500K tokens/day per account for `llama-3.1-8b-instant`.
- **Rate-limit headers do NOT expose daily remaining** — only the per-minute bucket (`limit=6000,
  reset=370ms`). You cannot read "tokens left today" from the API; use the Groq console dashboard.
- **`app-store-scraper` is broken** (non-JSON from Apple) → we use the iTunes RSS feed. RSS caps at
  10 pages × 50 = 500/country; **page 11 returns HTTP 400/500** (expected, not a bug).
- **Windows cp1252 console crashes on non-ASCII** (★, ✗, em-dash) in `print`. Always
  `sys.stdout.reconfigure(encoding="utf-8")` in scripts that print review text or symbols.
- **Token-count logging bug (fixed).** `classify_records` yields per-batch `pt/ct` for *every* record;
  an earlier `tot += pt+ct` per-record inflated the logged token count ~25×. The **per-key** numbers in
  the status file are the truth. If a log shows ~1900 tokens/review, it's the old bug — real is ~66–77.
- **`langdetect` is unreliable under ~20 chars** — short texts are decided by script (Latin → English)
  in `is_english()`, and texts with no letters (emoji-only) return True so junk-routing handles them.
- **The dashboard prototype `data.js` has a `crosswalk` field that is NOT in the contract and NOT
  rendered.** Do not build a crosswalk tab; the question→section mapping is deliberately invisible.
- **Hyphenated phase folder names** (`phase-4-layer1-broad`) aren't normal Python identifiers. Running
  via `python -m phases.phase-4-layer1-broad.classify` works; cross-imports between sibling phase files
  use `importlib.util.spec_from_file_location` (see `spotcheck.py`).
- **"golden set" ≠ "gold set"** (terminology trap from the brief). *Golden set* =
  `phases/phase-0-foundations/golden_set.jsonl`, 27 **synthetic** examples that test the deterministic
  filter. *Gold set* = the 50 **real, user-labeled** reviews for LLM-accuracy validation. They are different things.
- **Groq rate limits are PER-MODEL pools, not per-account-total.** 8B (`llama-3.1-8b-instant`), 120B
  (`gpt-oss-120b`), and 20B (`gpt-oss-20b`) each have their **own** daily budget. Exhausting one doesn't
  block the others — this is what let Phase 5 (120B) run while the 8B was dead. The 120B pool DOES exhaust
  after ~700K tokens/day across all keys; the 20B is a fresh fallback pool (`GROQ_MODEL_DEEP_FAST` in config).
- **gpt-oss models use a hidden "reasoning" channel.** With a trivial prompt + small `max_tokens` they
  return EMPTY visible content (tokens go to reasoning). Always use `response_format={"type":"json_object"}`
  + `reasoning_effort="low"` + generous `max_tokens`; then the answer lands in `message.content`.
- **The discovery sub-theme codebook has genuinely fuzzy boundaries.** Human–model agreement is 73%
  (≥1 theme overlap) but strict primary-theme accuracy is only ~40% / kappa 0.33 — `control`↔`autoplay`,
  `shuffle`↔`freegate`, `love`↔`dj` bleed. This is documented in `limitations`, not hidden. Counts shift
  somewhat between adjacent themes; the ranking/story is robust.
- **A German review leaked the English filter** (`langdetect` Latin-script fallback keeps it). Caught in
  the gold set; reported as a `languageCheck` false-keep. Filter is lenient by design (keeps Hinglish/slang).
- **The dashboard `dist/index.html` will NOT open via `file://`** (browsers block ES-module scripts over
  file://). Must serve it: `npm run dev` (:5173) or `npm run preview` (:4173). The Claude_Preview panel
  viewport is narrow (~350–560px) — use `preview_resize width:1340` before screenshotting or it looks cramped.

---

## 6. CONVENTIONS

- **One folder per phase** under `phases/` (Android + shared track-parameterized scripts) and under
  `ios/` (iOS-exclusive code, see D20), each self-contained with a `README.md` (Objective / Inputs /
  Steps / Outputs / Contract fields produced / Tests run / Exit criteria / Checkpoints / How to re-run).
  Shared code only in `common/`; a script that already handles both tracks via a `track` arg is never
  forked into a second per-track copy.
- **Re-target the whole tool by editing `common/config.py`** (app ids, countries, window depth,
  thresholds, taxonomy, model ids, key lookup). Don't hardcode elsewhere.
- **Run pattern:** `./.venv/Scripts/python.exe -m phases.<phase-pkg>.<module> [args]`.
- **Secrets:** `.env` (gitignored) holds `GROQ_API_KEY`, `GROQ_API_KEY_2/3/4` (one per Groq account).
  `.env.example` documents the format. `common/config.groq_api_keys()` collects them.
- **Testing approach:** (a) `phases/phase-2-filtering/test_golden.py` asserts the filter against the
  27-example golden set; (b) `phases/phase-4-layer1-broad/spotcheck.py` is the reusable LLM-agreement
  test (`build` / `validate` / `score <file>`), multi-label overlap scoring, ground truth in
  `data/interim/spotcheck_groundtruth.json`; (c) `python -m common.contract <snapshot.json>` validates
  an emitted snapshot. No pytest suite; tests are runnable scripts.
- **Long LLM/scrape runs:** background, **resumable by id**, with a `{track}_layer1.lock` (prevents
  double-append) and a `{track}_layer1_status.json` checkpoint (done/remaining/per-key tokens/complete).
- **Git:** **still not initialized** as of this handoff. The user wants a push to
  `https://github.com/spotifyscrapernextleap/Spotify-Review-Analysis-Scraper.git`. **Before any push,
  VERIFY `.gitignore` excludes `.env` (REAL Groq keys!), `.venv/`, `node_modules/`, `dist/`, and
  `data/raw/` (387k-review files).** A `.gitignore` exists — confirm it covers all of these first.
- **Deploy:** Vercel intended (user handles auth). `phases/phase-8-dashboard/dist/` is the build to ship.
- **Dashboard:** `phases/phase-8-dashboard/` is a Vite app (`npm install` → `npm run dev`/`build`). Its
  data is `src/review_data.json` (copy of `data/REVIEW_DATA.android.json`). `.claude/launch.json` has a
  `dashboard` preview config on port 4178.

---

## 7. OPEN THREADS / TODOs

**Android track is DONE through Phase 8 AND a v3 revision + full dashboard revamp** (see §4 D16–D19). The
discovery deep-dive is now v3 (1,462 confirmed, gpt-oss-120b); the snapshot + all four dashboard sections read
v3. The remaining work, in priority order:

- **1) Rebuild `dist/`.** Deliberately held during the iteration so the build wasn't frozen mid-change. Run
  `cd phases/phase-8-dashboard && npm run build` before deploy. The dev server (port 4178) already reflects
  everything; only the committed `dist/` is stale.
- **2) Git init + push** to `https://github.com/spotifyscrapernextleap/Spotify-Review-Analysis-Scraper.git`.
  ⚠️ FIRST verify `.gitignore` excludes `.env`, `.venv/`, `node_modules/`, `dist/`, `data/raw/` (see §6).
- **3) Phase 9 — Vercel deploy.** Build `dist/` first; user handles Vercel auth. Footer already shows
  "Android track · Real data". Write the top-level repo `README.md`.
- **4) iOS track — COMPLETE through Phase 7 (2026-07-02).** Built under a top-level `ios/` folder mirroring
  `phases/` (see D20); `ios/README.md` is the entry point. `scout_ios.py`/`collect_ios.py` moved to
  `ios/phase-1-collection/`. Pipeline run end-to-end:
  1. **Layer-1 census** (shared `classify.py track=ios`, hardened v5 tenets) — 2,105 classified;
     distribution near-identical to Android (pricing 52.6%, discovery 15.5%, ux 13.8%, tech 13.5%);
     genuine per-country us/gb/ca/in/au; 187 discovery. → `data/interim/ios_layer1.jsonl`.
  2. **Recall recovery** (`ios/phase-4-layer1-broad/recover_discovery_ios.py`, 120B census of ux+updates) —
     +14 recovered → pool 201. → `ios_discovery_pool.jsonl`, `ios_recover_summary.json`.
  3. **Phase 5 v3 deep-coding** (`ios/phase-5-layer2-discovery/recode_v3_ios.py`, gpt-oss-120b, imports the
     shared codebook) — 201→117 kept/84 not-discovery (41.8%, matches 8B over-tag); replicates Android v3
     (control #1 29.1%, love 22.2%, imposed repetition 25:0); emerging 6.8% → v3 fits iOS.
     → `ios_recode_v3_{coded,dropped}.jsonl`, `ios_recode_v3_analysis.json`.
  4. **Phase 6 gold** (`ios/phase-6-gold-validation/`, 25-review user-labeled sheet) — overlap 58.3%,
     kappa 0.348 (in line with Android's 0.33); main divergence control↔freegate framing; 1 flagged
     codebook gap (AI-generated music, n=1, noted not re-coded). → `gold_subtheme_scores_ios.json`.
  5. **Phase 7 snapshot** (`ios/phase-7-analysis-snapshot/build_snapshot_ios.py`) — census-exact, trends=[],
     no window/trend, platforms=null. VALIDATES against `common/contract.py` + cross-checks.
     → **`data/REVIEW_DATA.ios.json`** (the second deliverable snapshot).
  EFFECT-SIZE NOTE: Android dropped effect size from its dashboard (not evaluator-facing) so Android was left
  untouched; iOS effect is measured on the gate-confirmed CLEAN discovery pool (117), not the raw Layer-1 tag,
  because ~45% of Layer-1 iOS 'discovery' are high-rated (4.63★) false positives that wash the gap to -0.02.
  Clean-pool effect = **-0.72 (95% CI [-1.01,-0.45])**, baseline 3.90.
  STILL OUT OF SCOPE (separate later effort): wiring `REVIEW_DATA.ios.json` into the Phase-8 dashboard
  (platform toggle/second page). NEVER merge iOS+Android into one cross-platform number (different time spans).
- **Optional — finish the v2 hand-code or re-validate gold against v3.** v3 (120B) supersedes the old 690-row
  Claude v2 code; no need to finish it. The 50-review gold matrix is kept as the honest v2 "before" picture
  (D19) — re-scoring it against v3 is optional polish, not required.
- **Stale-but-unrendered:** the snapshot still carries the full `evaluation.*` block (sampling/funnelReconcile/
  abstention/languageCheck/goldComposition) because the contract requires it, but the revamped Methodology only
  renders sampling + fieldIntegrity + confusion. The unrendered ones (incl. the projected funnelReconcile) are
  harmless but could be cleaned if the contract is ever relaxed.
- **ToS:** multi-account Groq usage is a conscious gray-area choice (see D7).

---

### Footer — files that go deeper (don't duplicate these)
- `architecture.md` — full phase-by-phase build plan, dependency graph, the two human checkpoints.
- `edge-cases.md` — 37 failure modes (EC-1…EC-37) with detection/mitigation, incl. the two-track ones.
- `build and design docs/README.md` — **the authoritative Data Contract** + dashboard structure + design tokens.
- `build and design docs/spotify_review_intelligence_brief_final.md` — conceptual source of truth.
- `build and design docs/dashboard-design-spec.md` — dashboard narrative/content spec.
- `build and design docs/eval-strategy-appendix.md` — the chosen evaluation checks.
- `common/contract.py` — the contract as runnable pydantic + cross-checks.
- `phases/phase-*/README.md` — what each phase did, with real numbers and re-run commands. Newest:
  - `phase-5-layer2-discovery/` — **`codebook_v3_REVISED.md`** (THE current codebook; autoplay/safe retired),
    **`recode_v3.py`** (the canonical gpt-oss-120b full re-code with the 3 guardrails),
    **`borderline_test.py`** (the blind 22-review test that drove v3), plus the v2 history
    (`codebook_v2_REVISED.md`, `recode_claude.py`, `closed_code.py`, `open_code.py`).
  - `phase-6-gold-validation/` — `build_subtheme_gold_set.py` + `score_subtheme_gold_set.py` (50-review gold;
    kept as the v2 "before" picture in the Methodology, see D19).
  - `phase-7-analysis-snapshot/build_snapshot.py` — emits `data/REVIEW_DATA.android.json` (contract-valid);
    now reads the **v3** analysis + adds the `funnel.*` real numbers, `methodology`, and quote sentiment/co-tags.
  - `phase-8-dashboard/` — the Vite/React/Recharts app (`src/sections/*`, `src/tokens.js`); all four sections
    revamped this pass (Overview, Evidence, Discovery, Methodology).
- **Key data artifacts:** `data/REVIEW_DATA.android.json` (THE deliverable snapshot, v3),
  `data/interim/phase5_recode_v3_coded.jsonl` (the 1,792 v3 records, 1,462 discovery + 330 dropped) +
  `phase5_recode_v3_analysis.json` (aggregated v3), `data/interim/android_layer1.jsonl` (the 23,508 Layer-1
  sample). Older: `phase5_recode_labels.jsonl` (the v2 690 Claude codings, superseded).
