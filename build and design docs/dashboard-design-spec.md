# Spotify Review Intelligence — Dashboard Design & Content Spec

*A companion to the project brief. The brief says what the analysis is and why; this says what the dashboard must show, in what order, and in what visual form. It is written to be pasted into a design tool and rendered. It encodes the agreed decisions: balanced framing (problem **and** delight), an effect-size figure with a confidence interval, segments and unmet needs as independent reads rather than slices, repetition handled as a narrative bridge, and a visible evaluation layer. Layout polish and exact styling are still a design-phase choice — this fixes the content and the narrative spine, not the pixels.*

**The spine, in one line:** size the problem → show it's not the whole story → go deep on discovery → let anyone check the evidence → show the work. Every section hands the reader to the next.

---

## Section 1 — Summary / Overview

The job of this page is to make three things true before the reader goes anywhere: the discovery problem is **real**, it is **sized against everything else**, and the analysis **looked at the good as well as the bad**. A reader should be able to stop here and already trust the headline.

### 1A. Problem sizing

- **Share of voice across the six categories.** What proportion of substantive reviews raise each category (Discovery & Recommendations, Playback/Technical, Catalogue, Audio Quality, Pricing/Account, UX/Navigation). This sizes discovery against every other complaint.
  - *Visual:* horizontal bar, sorted, discovery highlighted.
  - *Rule:* every percentage carries its raw count beside it (e.g. "Discovery — 18% (n=361)"). A percentage without an n is not a finding.

- **Rating comparison — the headline effect size** The overall baseline star rating versus the average rating of reviews that mention discovery. The gap is the single most important number in the project, so it does not appear as a bare figure.
  - *Visual:* two values with the gap called out
  - *Why it's here:* this pre-empts the first challenge a sharp reader makes — "is that gap real or just chance?"

- **Rating distribution (the baseline).** The full 1–5 star histogram across all rated reviews, including contentless ones. This is the least-biased sentiment signal because it doesn't depend on who chose to write paragraphs.
  - *Visual:* simple star histogram, labelled as the baseline everything else is measured against.

- **Discovery share of voice over time.** A line showing how the discovery-mention rate moved across the analysis window. "Rising," "flat," or "falling" is a far stronger statement than a single snapshot, and the data already exists from the date-window work.
  - *Visual:* single line, analysis window shaded. A one-line read-out of the direction.

### 1B. Delight (the counterweight — kept deliberately light)

This block exists so the dashboard reads as an honest assessment rather than a prosecution. It is **intentionally shallow** — a counterweight, not a second investigation. No deep taxonomy.

- **How many reviewers are positive.** The overall share of positive / delighted reviews. One number, plainly.
- **Which categories drive the positive sentiment.** Category-level only — this falls out of the broad-pass sentiment already being computed, so it costs nothing extra.
  - *Visual:* a small bar of positive-sentiment share by category.
- **Top delight themes.** The three or four most common reasons people are happy, from a single light pass. Not ranked exhaustively, not sub-coded — just named, with counts.

### 1C. Discovery sentiment, in context (resolves the "reusable instrument" requirement)

Rather than a separate all-categories tab that nobody visits, the reusability proof lives here as a single contextual comparison: **the positive-versus-negative sentiment split within Discovery & Recommendations, shown alongside the same split for the other five categories.**

- *What it answers:* not just "is discovery a problem," but "is discovery *unusually* a problem, or do people grumble about everything equally?" Seeing discovery's negative share against catalogue's, pricing's, playback's, etc. is what makes the discovery claim land.
- *Visual:* a stacked or diverging bar per category showing positive vs negative share, discovery highlighted. All six categories appear, so the "this engine classifies everything, not just discovery" claim is made implicitly — no dead tab required.
- *Light add-on:* the common themes inside the **positive** discovery reviews (kept shallow, same spirit as 1B) — so the deep dive isn't the first time the reader sees that some people genuinely love discovery.

> **Narrative handoff to Section 2:** the overview ends having proven discovery is real, sized, and not universally hated. The natural next question is *why* — for the people who are frustrated, what exactly is going wrong, and what were they trying to do in the first place. That is the deep dive.

---

## Section 2 — Discovery Deep Dive

This is the primary investigation. It is built as a **narrative in three buckets**, with a bridge between them and two independent parallel reads hanging off the side. There is no visible "six questions" crosswalk — the data points to the answers; it never announces them.

### The structure

**Bucket 1 — Listening behaviour.** What users are trying to *achieve* — the goals and contexts they describe (workout, focus, sleep, discovery sessions, background, mood). Marked exploratory, because reviews disclose goals only sometimes.

**↓ The repetition bridge (this is where "listening to the same music again and again" lives)**

Repetition is **not** a fourth bucket — it's the hinge that connects behaviour to problems. The visual is a single split:

```
        "Users listen to the same music repeatedly"
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
   CHOSEN repetition            IMPOSED repetition
   (a need, not a fault)        (a discovery/rec failure)
   • comfort listening          • filter bubble
   • mood / habit               • shuffle that isn't random
   • intentional replay         • recommendations too "safe"
            │                           │
   flows into unmet needs       flows into Buckets 2 & 3
```

- *What it does:* it turns repetition from an orphan into the most interesting turn in the story — the same observed behaviour splits into "something we should respect" and "something we should fix." The right branch is the on-ramp into the two problem buckets below.
- *Visual:* a two-branch split diagram with review counts on each branch.

**Bucket 2 — Problems with new music discovery.** The sub-themes of *finding* new music: the 5–6 consolidated sub-themes plus the "other / emerging" escape hatch.
- *Visual:* ranked horizontal bar, counts shown, "emerging" bucket visible so the reader sees nothing was force-fit.

**Bucket 3 — Problems with the recommendation system.** The sub-themes of *what gets served*: again the 5–6 consolidated sub-themes plus the escape hatch.
- *Visual:* ranked horizontal bar, same treatment.

### Two independent parallel reads (NOT slices of the buckets)

Both of these are read off the same pool of discovery reviews as **flat, standalone reads**. They do **not** subdivide the sub-themes above — this is the deliberate decision to avoid splitting 360 reviews into ever-thinner cells until the numbers become noise.

- **Unmet needs.** A separate ranked synthesis of the needs that recur across the discovery reviews, inferred independently of the sub-theme tagging. A flat list, ranked by frequency.
- **User segments (use cases).** A separate, exploratory read of the use cases users disclose in their own words, inferred independently of the sub-themes. Flat, ranked, and **clearly labelled exploratory with partial coverage** — only some reviews reveal a use case.
  - *Display rule for both:* show counts, and flag any item resting on a thin base ("directional, low n") rather than presenting it with false confidence.

> **Narrative handoff to Section 3:** every theme, need, and segment above is a claim. The reader who wants to verify any of them clicks through to the evidence.

---

## Section 3 — Evidence Explorer

The receipts layer, pulled out as its own section so the narrative sections stay clean and the proof stays one click away.

- A browsable, filterable list of the underlying review quotes.
- **Filter by:** category, discovery sub-theme, sentiment (positive / negative), and — as secondary slices — platform (iOS / Android) and country.
- Each quote shows its **evidence snippet** (the exact text that justified the tag), its assigned theme, and its sentiment.
- *Why it earns its own section:* it lets the curated story upstream stay uncluttered while giving a skeptical evaluator a way to pull any thread and check it against raw text.

---

## Section 4 — Methodology & Evaluation

Two layers. The methodology is the always-visible "here's how this was built." The evaluation sits one click deeper, for the reader who wants to pressure-test the numbers.

### 4A. Methodology (visible)

Presented as visuals, not paragraphs:

- **The collection funnel** — collected → deduplicated → English → substantive → discovery → deep-coded, with the count removed at each step.
- **The denominators**, stated explicitly: which figures are shares of *all* reviews and which are shares of *substantive* reviews.
- **The gold-set accuracy headline** — the single agreement number, with the per-category detail available in the eval layer.
- **The date-window justification**, with the volume-over-time chart as the exhibit (the same data surfaced in 1A, here used to justify the window choice).
- **How the sentiment baseline is computed**, in plain terms.
- **Limitations, stated plainly:** reviewers are not all users; chronic, low-grade dissatisfaction is structurally undercounted (so a modest discovery number is not a small problem); segment coverage is partial; English-only; the window is recency-bounded.

### 4B. The evaluation layer (one click deeper)

A link at the foot of the methodology leads here. *(Title to be chosen — see the rename options.)* This is where the quality checks become pictures rather than promises. The principle: an eval the evaluator can *see* beats one they have to take on trust.

1. **Sampling fairness.** Collected star-distribution overlaid against each store's publicly reported distribution, with the gap stated as a number.
   - *Visual:* paired / overlaid bar. The comparison is the point — never the collected distribution alone.
2. **Funnel reconciliation.** The same funnel as 4A, but here the arithmetic is shown to conserve at every step (in = out + removed).
   - *Visual:* funnel chart with per-step removal counts annotated.
3. **Field integrity.** A data-health row: % valid records, count quarantined, broken out by field, so a missing rating is shown to have been quarantined rather than silently coerced to zero.
   - *Visual:* small stat cards.
4. **Language-filter spot-check.** The measured false-drop and false-keep rates of the English filter, with one Hinglish / code-switched example beside them.
   - *Visual:* two numbers plus a worked example.
5. **Per-category accuracy (the centrepiece).** The classifier's labels against the gold set as a confusion matrix, with Discovery's row/column highlighted and its standalone accuracy called out. This single chart does the most work for credibility.
   - *Visual:* heatmap confusion matrix.
6. **Gold-set composition.** Shows the set was deliberately weighted toward the hard borderline cases (short-but-substantive, long-but-empty) and covers all six categories, so the accuracy number isn't flattered by easy examples.
   - *Visual:* stacked bar — borderline vs easy, and coverage per category.
7. **Abstention calibration.** Accuracy of the model's confident labels versus its abstained / uncertain ones, demonstrating that confidence tracks correctness.
   - *Visual:* paired bar.

> **Narrative close:** by the end, the reader has seen the problem sized, the balanced picture, the deep diagnosis, the raw evidence, and the proof that the machinery underneath is sound. Nothing is asserted that can't be checked.

---

## Appendix — what each part quietly answers

*(For your reference only — not a section in the dashboard. The crosswalk is deliberately invisible to the reader; this is just so you can confirm coverage.)*

- Q1 (why discovery struggles) → Bucket 2
- Q2 (recommendation frustrations) → Bucket 3
- Q3 (behaviours users want) → Bucket 1
- Q4 (repeated listening) → the repetition bridge
- Q5 (segment differences) → the independent segments read (exploratory)
- Q6 (unmet needs) → the independent unmet-needs read

A light, unobtrusive tag on each deep-dive element ("addresses recommendation frustrations") is enough to let a checking evaluator confirm coverage without a crosswalk section ever appearing.
