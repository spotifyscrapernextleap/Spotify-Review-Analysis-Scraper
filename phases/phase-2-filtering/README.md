# Phase 2 — Normalisation & Filtering (the guardrails)

**Objective:** deterministically clean the raw corpus into Tier A/B/C — routing, never deleting. No model involved.

**Runs per track, independently:** `filter_reviews.py <android|ios>` reads `data/raw/{track}_raw.jsonl` and writes `data/interim/{track}/…` + `data/interim/{track}_filter_report.json`. Same deterministic logic for both; the Android sampling happens later (Phase 4), not here.

**Inputs:** `data/raw/{track}_raw.jsonl` + `{track}_manifest.json` (Phase 1); `phases/phase-0-foundations/golden_set.jsonl`.

**Steps (order chosen cheapest-and-most-eliminating first, with one deliberate reorder):**
1. **Field integrity** — validate rating (1–5 int), date, country; empty text is *valid* (Tier C), not a quarantine reason. Malformed records are quarantined + **counted, never coerced** (EC-9).
2. **Dedupe** — conservative: only collapse reviews identical after normalisation **and ≥ 8 words** (true reposts). Short ratings ("good") are never deduped — they are separate baseline data points; collapsing them would corrupt the star baseline (EC-10).
3. **Language filter** — drop confident non-English. **Junk-safe ordering:** short texts decide by script (langdetect is unreliable < 20 chars), and a Latin-script + English-token fallback deliberately KEEPS Hinglish/slang (the false-keep the eval layer later quantifies, EC-8).
4. **Junk / tier routing** — emoji-only, char-repeat, single-word, sentiment-only, spam, and empty text → **Tier C** (contentless: counted, star retained, never sent to a model). Everything else → **substantive candidate** (final Tier A/B split rides on Layer-1 categorisation, Phase 4).

**Outputs / artifacts (per track):**
- `data/interim/{track}/substantive_candidates.jsonl`, `tierC.jsonl`, `quarantined.jsonl`
- `data/interim/{track}_filter_report.json` (funnel + field integrity + dedupe/language counts + Tier-C reasons)

**Contract fields seeded:** `funnel.deduplicated/english/tierC`; `evaluation.fieldIntegrity`; collection rows of `evaluation.funnelReconcile`.

**Tests run:**
- **Golden-set test (`test_golden.py`) — Phase 2 gate:** ✅ **27/27** dispositions correct. Guarantees no tierA/B signal is false-dropped (esp. short-but-substantive g11 and Hinglish/slang g24/g25), non-English is flagged, obvious junk → Tier C, and the near-dupe pair collapses.
- **Dedupe legitimacy check:** ✅ on the earlier combined corpus, 100% of dedupe groups were **cross-country** reposts — confirming we're not over-merging.
- **Funnel reconciliation (EC-22):** asserted `in = out + removed` at every step, per track.

**Funnel results:**
- **iOS** (snapshot): collected 2,500 → id-dedup 2,500 (0 — genuinely per-storefront) → english 2,398 (−102) → **substantive candidates 2,106** + Tier C 292.
- **Android** (6-month census): collected **387,086** → **id-dedup 129,045** (−258,041 = the cross-"country" triplication; google-play's country param returns the same global stream 3×, so country is relabeled `global`) → text-dedup 129,018 (−27) → english 124,597 (−4,421 non-English) → **substantive candidates 96,822** + Tier C 27,775.
  - The 96,822 is the *census* substantive denominator; Phase 4 will LLM-classify a stratified **~2k/month sample** of it, not all of it.

> **Key finding:** google-play-scraper's `country` param does NOT segment reviews — 129,012 of 129,045 reviewIds appeared in all 3 country pulls. Android "country" is therefore not a real dimension (unlike iOS); the true unique Android corpus is ~129k. Dedupe is by underlying reviewId (exact identity), which also prevents 3× inflation of short reviews in the star baseline.

**Exit criteria:** ✅ golden test passes; funnel reconciles; dedupe verified legitimate; substantive corpus (7,044) well above the saturation reference.

**Checkpoints / human input:** none.

**How to re-run:**
```bash
./.venv/Scripts/python.exe phases/phase-2-filtering/test_golden.py
./.venv/Scripts/python.exe -m phases.phase-2-filtering.filter_reviews ios
./.venv/Scripts/python.exe -m phases.phase-2-filtering.filter_reviews android
```
