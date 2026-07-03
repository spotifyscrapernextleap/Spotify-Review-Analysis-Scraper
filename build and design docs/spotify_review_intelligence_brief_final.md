# Spotify Review Intelligence — Project Brief

*A conceptual brief. It defines the idea, the reasoning behind it, the stages it moves through, and every decision already settled. It deliberately does not prescribe the technical build — model wiring, libraries, and implementation choices are left to Claude Code. The dashboard's required contents, narrative, visual design, and the exact data the pipeline must emit are now settled too, but they live in the companion documents below rather than here.*

## 0. Companion Documents — read these alongside this brief

This brief is the **conceptual source of truth**: the idea, the reasoning, and every settled decision. Three companion docs sit in the same project folder and are authoritative for the detail this brief does not duplicate. Where a companion doc specifies something more precisely than this brief, **the companion doc wins.**

- **`README.md` — the build handoff and the binding interface.** Authoritative for: the **Data Contract** (the exact `window.REVIEW_DATA` JSON object the pipeline must emit — this is the contract between the scraper/analysis half and the dashboard half), the four-section dashboard **structure**, the **design tokens** (colour, type, spacing), and per-screen specs. *If the pipeline emits the contract's shape, the dashboard renders with no changes.* Start here after this brief, and read the Data Contract first.
- **`dashboard-design-spec.md` — the narrative/content spec.** Authoritative for *what each dashboard section shows, in what order, and why* (the problem-sizing spine, the delight counterweight, the three-bucket deep dive, the repetition bridge, the evidence and evaluation layers).
- **`eval-strategy-appendix.md` — the chosen quality checks.** Authoritative for *which* evaluation checks were selected and the reasoning behind each (collection-layer and classification-layer). Slots in before Section 10.

**Reading order for the build:** this brief → `README.md` (Data Contract first) → `dashboard-design-spec.md` → `eval-strategy-appendix.md`.

---

## 1. The Idea

A tool that collects publicly available Spotify reviews from the iOS App Store and the Google Play Store, filters them down to genuine signal, and turns that signal into a defensible, evidence-backed picture of how users experience **music discovery** and **listening behavior** on the platform. (Reddit and other forums are deliberately out of the pipeline — see Section 5; any Reddit reading is optional, off-pipeline scouting only and produces none of the data the build consumes.)

It has two faces. The primary one is a focused investigation into discovery and recommendation behaviour — the heart of the assignment. The secondary one is a general-purpose review-sentiment instrument that classifies *all* feedback into broad categories, so the same pipeline can speak to technical, catalogue, quality, pricing, and usability sentiment, not just discovery. The second face is what makes this a reusable tool rather than a one-off study.

The output is a single shareable dashboard, backed by a documented repository, that an evaluator can open and interrogate.

## 2. Why We Are Doing It

The brief hands us a problem already labelled as a problem: *significant percentage of listening still comes from repeat playlists, familiar artists, previously discovered tracks, and Spotify want to increase meaningful discovery and reduce repetitive listening behavior.* The first move is to refuse to take that on faith. Before dissecting the problem we **size it** — we ask how many users actually raise discovery as a concern, unprompted, and how strongly they feel about it. That reframes the whole exercise from "I analysed some reviews" to "I validated whether the stated problem is real, established how big it is, and only then went deep." Problem validation before solution exploration is the spine of the work.

This is **preliminary research**, so it runs without a pre-baked hypothesis. We do not decide in advance *why* people re-listen or *why* discovery fails and then go hunting for confirmation. The themes emerge from the data; our six questions enter only at the end, as the lens through which we read what emerged.

## 3. Guiding Principles

These govern every decision downstream and should survive into the build:

- **Size the problem before dissecting it.** The prevalence of an issue is established before its anatomy.
- **Let themes emerge.** No imposed hypothesis. Structure is *derived* from the data, not pre-loaded onto it.
- **Be honest about what reviews can and cannot answer.** Some questions the data answers strongly; others only directionally. The brief says which is which, and the dashboard does too.
- **Measure quality, do not assume it.** The reliability of the automated categorisation is validated against a hand-labelled set and reported as a number, not hoped for.
- **Nothing is deleted, only routed.** Every review participates in whatever analysis its content can support. A review with no usable text still contributes its star rating. The right denominator is chosen for each question rather than forcing one denominator on all of them.
- **Reusable and testable are the success criteria**, not scale of data. A defensible 2,000 reviews beats an indefensible 50,000.

## 4. The Questions It Must Answer

The investigation exists to answer six questions:

1. Why do users struggle to discover new music?
2. What are the most common frustrations with recommendations?
3. What listening behaviours are users trying to achieve?
4. What causes users to repeatedly listen to the same content?
5. Which user segments experience different discovery challenges?
6. What unmet needs emerge consistently across reviews?

A candid note carried through to the output: reviews answer questions 1, 2, 4, and 6 well, because users complain about these directly and in volume. Questions 3 and 5 — what users are *trying to achieve*, and how *segments* differ — are answered only **directionally**, because reviews do not reliably state goals or personas; those findings rest on the subset of reviews that disclose usage context. They are presented as exploratory, with that limitation visible.

## 5. Scope — Settled

**In scope**

- **Two sources only:** the iOS App Store and the Google Play Store. These two carry the overwhelming majority of the usable signal, and they are the only sources the data contract (README) represents.
- **English only, across multiple country stores** (e.g. US, UK, India, Canada, Australia) to maximise volume.
- **Depth over breadth:** roughly **2,000 substantive reviews**, sized by thematic saturation — the point at which new reviews stop producing new themes — rather than by collecting everything.
- **A derived date window, not a fixed one.** Rather than asserting "90 days," we collect a wider net (around twelve months), observe how review volume and average rating move over time, and then choose an analysis window (likely around six months) that spans several app-update cycles so no single release dominates, is recent enough to reflect the current product, and yields enough volume to reach saturation. The choice is justified in writing, with the volume-over-time view as the exhibit. The collection method itself differs by store — iOS exposes a recent rolling window while Android can be retrieved further back — which is part of why the window is derived from what the data actually supports rather than fixed up front.
- **Usage-based segmentation, inferred from the reviews themselves.** Segments are not geographic. They are the *use cases users disclose* in their own words ("I use it at the gym," "for studying," "as someone who makes playlists"). This is treated as a light, exploratory dimension with partial coverage. Country is retained as a free secondary slice but is not the story.
- **Balanced platforms.** iOS and Android are sampled to roughly balance, so neither platform's voice drowns the other and platform remains available as a comparison slice — without making platform the headline.

**Out of scope (for this version)**

- **Social media (X, Instagram, etc.) and community forums (incl. Reddit / r/spotify).** These are where this kind of project quietly dies — locked-down access, high effort, low marginal signal. Excluded from the pipeline deliberately. Reddit may be read informally to sharpen intuition during design, but it is **off-pipeline**: it contributes no collected records, no counts, and no data-contract fields, so it can never desync the analysis from what the dashboard renders.
- **Any claim that reviewers represent the user base.** The analysis describes reviewers, not all Spotify users, and says so.

## 6. The Stages

The workflow moves through five stages. Each is described by what it does and the decisions already made about it; the technical means are for the build to determine.

### Stage 1 — Collection

Gather reviews from both stores, in English, across the chosen countries, over the wider (≈12-month) net. Collection is polite by design — it paces itself and tolerates interruptions — and it respects the differing reach of each store. The raw haul is expected to be a few thousand reviews, the majority of which will not survive filtering.

### Stage 2 — Normalisation and Filtering (the guardrails)

Before anything intelligent happens, the data is cleaned by deterministic rules — no model involved, so this stage is effectively free and fast. The logic, in order of cheapest-and-most-eliminating first:

1. **Deduplicate** — exact and near-duplicate text removed (the same review can appear across multiple country stores).
2. **Language filter** — keep English only.
3. **Substance gate** — does the review carry a codeable claim: something specific enough to attach a category or theme to? This is a judgement about meaning, not length. Word count is an unreliable proxy in both directions — "shuffle isn't random, repeats songs" is codeable in six words, while a rambling twenty-word review can carry nothing — so the gate is decided on content, not on a word threshold. The golden set defines that boundary by example, and because a review that no category can be assigned to is by definition non-substantive, this judgement can ride on the categorisation step itself rather than needing a separate length rule. (How it is detected in practice is left to the build.)
4. **Junk rules** — emoji-only, repeated-character strings, single sentiment words, spam.

Filtering routes rather than deletes. Reviews fall into three tiers:

- **Tier A — deep-codeable:** substantive enough for theme work; travels the full pipeline.
- **Tier B — categorisable but thin:** short, but a category and sentiment can still be assigned; contributes to category and sentiment counts only.
- **Tier C — contentless:** no usable text; never sent to a model; **counted**, and its **star rating retained** as part of the sentiment baseline.

How the tiers map to the funnel (README): obvious contentless/junk reviews (Tier C) are caught here by deterministic rules and never sent to a model. For the borderline remainder, the substance judgement *rides on* Layer-1 categorisation — a review that earns a category is substantive (Tier A/B); one that earns none is routed to Tier C. So the Tier split in the funnel is partly deterministic and partly an output of the broad categorisation pass; it is not a separate standalone model stage. (`substantive = tierA + tierB` in the contract.)

The rules are anchored by a small **golden set** of worked examples — clear keep, clear junk, and the tricky borderline cases (short-but-substantive, long-but-empty) — which both guides the filter and serves as a way to test that the filter behaves correctly.

The principle to hold: contentless reviews are not analytical content, they are denominator and baseline infrastructure. The words may leave; the stars stay.

### Stage 3 — Categorisation (the brain)

Two layers, built so the model's job is to *classify against a given list* rather than to *invent*, because that is where automated classification is reliable.

**Layer 1 — broad categorisation.** Every substantive review is filed into one of six fixed top-level categories — Discovery & Recommendations, Playback/Technical, Catalogue/Song Availability, Audio Quality, Pricing/Account, UX/Navigation — and given a sentiment. This is the cheap, high-volume pass, and it produces the general cross-category view. (The data contract also defines an `other` top-level id as a catch-all for substantive reviews that carry a codeable claim but fit none of the six cleanly; see README `categories`. Decide during the build whether `other` is populated or left empty, but keep the id available so the contract shape holds.)

**Layer 2 — deep coding within Discovery.** This is the differentiated work, and it follows the emergent-then-codified path:

1. **Open pass on a small sample** — themes are allowed to surface freely from a modest sample of Discovery reviews.
2. **Consolidation into a codebook** — those raw themes are reviewed and collapsed, by hand, into a clean fixed list of Discovery sub-themes. This is where human judgement does the work the model cannot be trusted to do alone.
3. **Closed classification at scale** — every Discovery review is filed against that fixed codebook, with a mandatory **"other / emerging"** escape hatch so genuinely new themes are not force-fit.

Throughout Layer 2, each tag is **grounded in an evidence snippet** — the exact piece of the review that justifies it — which both reduces hallucinated intent and supplies real quotes for the output. The model is allowed to **abstain** ("unclear / low confidence") rather than guess. The **implied use case** is extracted as a light tag-along wherever a review reveals one.

The integrity of "emergent themes" is preserved because the themes genuinely came from the data in step one; they were merely stabilised before scaling. This is standard qualitative coding — open coding, then a codebook, then closed coding — not a shortcut.

The codebook's *content* is derived here, but the *shape* it must fit is already fixed by the data contract and is not open to reinvention: each sub-theme is an object carrying a `group` (`repetition` | `relevance` | `features` | `positive`); the repetition sub-themes form a highlighted cluster; the sub-themes map into exactly two problem buckets (finding vs recommendations) plus an `emerging` escape-hatch count; and repetition is rendered as the chosen-vs-imposed bridge. Build the codebook to populate that shape (see README `discovery`, `buckets`, `bridge`; rendering in `dashboard-design-spec.md` §2).

**Validation.** Around fifty reviews are hand-labelled as a gold set. The pipeline's labels are compared against them and reported as the project's answer to "is the automated categorisation good enough?" — measured, not assumed. Agreement is reported both as a raw rate and as a chance-corrected statistic (the contract carries `kappa`), and broken out **per category** rather than as one blended number, so Discovery's own accuracy is visible. The specific checks and their reasoning are in `eval-strategy-appendix.md` (classification-layer checks 5–7); the reported fields are in README `validation` and `evaluation`. *Note:* fifty reviews across six categories with a deliberate borderline weighting yields a thin per-category base (≈8 each), so per-category accuracy is directional — grow the set if the build has room, and flag any thin cell rather than over-claiming.

### Stage 4 — Analysis and Metrics

From the categorised data, the following are computed:

- **Topic prevalence / share of voice** — the proportion of reviews raising each category, which sizes the discovery problem against every other problem. Prevalence is always reported against a **stated denominator**, and where it matters both denominators are shown: as a share of *all* reviews and as a share of *substantive* reviews.
- **Sentiment baseline** — the distribution of star ratings across *all* rated reviews, including the contentless ones. This is the benchmark, and it is the least-biased sentiment signal available because it does not depend on who chose to write.
- **Effect size** — the gap between the overall baseline rating and the rating of reviews that mention discovery. Both groups are drawn from the same biased reviewer pool, so the bias largely cancels and the *gap* is meaningful even though the absolute level is not a population truth. 
- **The Discovery findings** — sub-theme frequencies; a focused view on repetition-related themes; a synthesis of recurring unmet needs; the desired behaviours users express; and the exploratory cut of themes by use-case segment.

A caveat carried into the analysis: discovery dissatisfaction is a *chronic, low-grade* failure mode, the kind people rarely write reviews about (unlike an acute crash or a price hike). So review-mention rates likely **understate** the true prevalence of the discovery problem. A modest number is therefore not evidence of a small problem; it is evidence that this data source structurally undercounts this class of problem.

### Stage 5 — Dashboard

The single shareable output. Its required contents and narrative are specified in `dashboard-design-spec.md`; its structure, visual design, and the exact data it consumes are specified in `README.md`. It reads from a **pre-computed snapshot** of the analysed data, so it stands alone without a live backend, and it is deployed as a shareable link with the repository documented so the workflow can be re-run.

The snapshot is not a free-form export: it is the single `window.REVIEW_DATA` JSON object whose schema is fixed in the README **Data Contract**. That schema is the binding interface between the pipeline and the dashboard — the pipeline's last job is to emit exactly that shape. **All counts, percentages, and statistics are pre-computed by the pipeline; the dashboard performs no analysis, only display.** The contract's golden rule mirrors this brief's own: every share/percentage field travels with its raw `n`.

## 7. The Analytical Engine — Decisions Made

These are settled choices and the reasoning behind them. The exact wiring, batching, caching mechanics, and verification of current limits are for the build to handle.

- **Two models, two jobs, on the Groq free tier.** The deep Layer-2 pass runs on the larger model (gpt-oss-120b), chosen for its more generous daily token budget — which buys room to *iterate* during development, not just to complete one clean run — and because it is the supported successor to the deprecated llama-3.3-70b. The cheap Layer-1 pass runs on a small fast model (llama-3.1-8b-instant), which draws from a separate quota.
- **The pipeline is designed to fit inside the free tier**, via four levers: filtering junk in code *before* any model is called, so no tokens are spent on noise; batching many reviews into each call; using two models so their quotas are separate; and caching the unchanging instruction-and-codebook prefix that rides on every call.
- **Live limits are verified against the actual usage dashboard before the full run**, because these caps move. Estimates are calibrated from a small real test, not trusted from documentation.
- **Deployment is a shareable hosted dashboard reading a committed data snapshot, with a documented repository.** Reusability comes from the workflow being parameterised and documented; testability comes from the live dashboard plus the reported gold-set accuracy. (Vercel is the intended host; the final stack is a build-phase choice.)

## 8. The Dashboard — What It Must Contain

The required contents, section order, and narrative are specified in **`dashboard-design-spec.md`** (the "why" and the content spine). The dashboard's **structure** (four fixed sections: Overview · Discovery Deep Dive · Evidence Explorer · Methodology & Evaluation), its **visual design** (colour, type, spacing tokens), and the **Data Contract** it consumes are specified in **`README.md`**. This brief does not duplicate either; treat both as binding. The one thing to carry in mind here: the dashboard's job is display, not analysis — if the pipeline emits the `window.REVIEW_DATA` object defined in the README Data Contract, the dashboard renders unchanged.

## 9. What "Done" Looks Like

- The dashboard opens by **sizing the problem** (Overview), lets a viewer go deep on the Discovery findings with evidence (**Discovery Deep Dive** + **Evidence Explorer**), and inspect the methodology and data-accuracy/eval strategy (**Methodology & Evaluation**). The general cross-category / reusability view is **not a separate tab** — it lives inside the Overview as the per-category sentiment-in-context comparison (`dashboard-design-spec.md` §1C). The four sections are fixed; see README "Screens / Views."
- The automated categorisation has a reported accuracy against a hand-labelled gold set.
- Every prevalence figure has a stated denominator; the effect-size gap is shown against the star baseline.
- The whole pipeline runs within the free-tier budget, confirmed against the live usage dashboard.
- The tool is shareable as a link and the workflow is documented well enough to be re-run with a different app, window, or taxonomy.
- The limitations are stated plainly rather than hidden.

## 10. Deliberately Left to the Build

**Still open — Claude Code decides and implements:**

- The collection mechanism for each store, and the precise field schema *of the raw scrape* (the *output* schema is fixed — see below).
- The exact filtering implementation and threshold tuning against the golden set, including how near-duplicate and substance detection are actually done.
- The prompting, batching, and caching mechanics, and the per-run token accounting.
- The model wiring and verification that the named Groq models still exist and what their live limits are (see Section 7).
- How the effect-size confidence interval is computed (bootstrap or analytic).
- The dashboard's **technology** — framework (React/Vue/Svelte/etc.) and a real charting library (Recharts/Visx/ECharts/D3) per README guidance — and all implementation detail behind the specified design.
- Repository layout, documentation format, and deployment configuration (Vercel intended).

**No longer open — specified elsewhere; do not improvise:**

- **The data-snapshot format** the dashboard reads from → fixed by the **Data Contract** in `README.md`. Emit exactly that shape.
- **The dashboard's structure** (four sections) and **content/narrative** → `dashboard-design-spec.md` + README "Screens / Views."
- **The dashboard's visual design** (colour, type, spacing, components) → README "Design Tokens." It is high-fidelity, not a free choice; recreate it in the chosen framework.
- **The evaluation checks** to compute and surface → `eval-strategy-appendix.md`.
