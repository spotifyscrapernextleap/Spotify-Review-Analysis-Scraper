# Evaluation Strategy — Selected Checks (Appendix to the Brief)

*An appendix to the project brief. It records the specific quality checks chosen for this build and the reasoning behind each. Like the rest of the brief, it states the decision and the why; the implementation — how each check is actually computed — is left to the build. This is a deliberately partial set: each check was chosen because it produces a visible, defensible signal, not because the catalogue was exhausted. It is designed to slot in before Section 10 ("Deliberately Left to the Build").*

A principle carried across all of them: **an eval the evaluator can see is worth more than one they have to take on trust.** Each check below is meant to surface as a stated number or exhibit in the dashboard's methodology section, not to sit silently in the repository. Rigour and *visible* rigour are different products, and a graded deliverable needs both.

\---

## Collection-layer checks — is the data fair, complete, and clean?

These guard the data *before* any model touches it. They matter disproportionately because they sit upstream of everything: a biased or broken collection silently invalidates every downstream number — including the classifier's measured accuracy, since the gold set is drawn from the same data the scraper collected. A clever classifier eval cannot rescue a poisoned scrape.

**1. Sampling-fairness check (the histogram).** The collected set's star-rating distribution is compared against each store's publicly reported rating breakdown. A close match is evidence the sample is representative of the store; a divergence is selection bias — for instance, a scraper that returns only the most-recent or most-helpful reviews. The size of any gap is reported as a stated number rather than left hidden. This is the first challenge a sharp reader raises, so it is answered pre-emptively.

**2. Funnel reconciliation.** The counts at each stage of the pipeline must conserve: collected equals deduplicated plus duplicates removed; deduplicated equals English plus non-English; and so on, down to deep-coded. An automated check confirms the funnel adds up at every step. Because these counts become the denominators behind every prevalence figure, a funnel that leaks is a denominator that lies.

**3. Field integrity.** Every collected record is validated against an expected shape — a valid, in-range date; a 1–5 integer rating; a country; and either review text or an explicit empty-text flag (Tier C). Malformed records are quarantined and *counted* rather than silently coerced, so a missing rating never quietly becomes a zero that drags the sentiment baseline down. The count of quarantined records is itself reported.

**4. Language-filter spot-check.** Because the scope is English across multiple country stores — India included — the English filter is spot-checked against a small hand-labelled sample to estimate how often it wrongly drops English (heavy slang, emoji) or wrongly keeps code-switched text (Hinglish). The measured error rate is noted as a known limit on the English-only claim, rather than the claim being asserted as clean.

\---

## Classification-layer checks — is the model sorting correctly?

These extend the gold-set validation already described in Stage 3.

**5. Per-category accuracy, not a single agreement rate.** The classifier's labels are compared to the gold set as a per-category breakdown — showing where each category's reviews actually land — rather than as one blended accuracy figure. This exposes specific confusions (Discovery bleeding into UX or Catalogue) that a single number conceals, and it lets accuracy *on Discovery* — the headline category — be reported on its own, since that is the number that matters most for this investigation.

**6. A gold set weighted toward the hard cases.** The hand-labelled set is deliberately constructed to cover the borderline reviews the brief already names — short-but-substantive, long-but-empty — and to give every one of the six categories enough examples to estimate its accuracy individually. A gold set of only easy cases reports a flattering number that means nothing; the boundary is exactly where the measurement has to be taken.

**7. Abstention calibration.** The model is permitted to abstain ("unclear / low confidence") rather than guess. This check verifies the abstention is meaningful: that the reviews flagged as uncertain are genuinely the ambiguous ones, and that the model's confident labels are measurably more correct than its unsure ones. If confidence does not track correctness, the signal is noise and is treated as such rather than reported as if it carried information.

\---

## A note on what was deliberately left out

This set is partial by choice, to keep the eval surface small enough to build and maintain well rather than broad and shallow. The following were considered and set aside for this version, and remain available if the build has room:

* **Analysis layer (none selected).** A confidence interval on the discovery effect-size gap, and a window-sensitivity re-run at 3 / 6 / 9 months, were both set aside. Worth revisiting first if time allows, because the effect-size gap is the project's single headline number and a bare figure invites the "is that just noise?" challenge.
* **Further classification checks.** A frozen gold set used as a regression suite on every prompt change; a human-agreement ceiling to anchor what a "good" accuracy even is; an evidence-grounding faithfulness check; and a batch-contamination / position-bias check. Each adds credibility but also surface area; deferred to keep the build focused.

The principle to hold: a defensible handful of checks, each producing a number the evaluator can see, beats a long list that is half-built and unreported.

