# Phase 4 — Layer-1 Broad Categorisation (iOS track)

**Objective:** classify every iOS substantive candidate into the multi-label taxonomy
(discovery/tech/ux/pricing/catalogue/audio/updates/other + none/podcast routing labels).

**Census, not sample:** unlike Android (23,508-review stratified sample out of 96,822
candidates, Phase 4 `sample.py`), iOS classifies its **entire** 2,106 substantive-candidate
pile — it's small enough, and D3's rule ("census what's free, sample what costs") still
applies since the iOS pile is far below what the free Groq tier can cover in one run.
`sample.py` has no iOS role.

**Code location — reused, not forked:** `phases/phase-4-layer1-broad/classify.py` is a single
script parameterised by `track`, carrying the hardened v5 prompt
(`PROMPT_VERSION = "v5-multilabel-2026-06-25"`) — the tenets from the Android reclassification
(multi-label 1-3 categories, `playback`→`tech` rename, `updates` additive, podcast-only
deterministic discard, ads ALWAYS→pricing, vague praise→`none` not `other`, smart-shuffle/
autoplay→discovery, casting/account-errors→tech). Running it with `track=ios` applies the
exact same prompt and rules to the iOS corpus — no separate classifier needed, and no drift
risk between the two tracks' definitions of each category.

**Inputs:** `data/interim/ios/substantive_candidates.jsonl` (Phase 2, 2,106 reviews).

**Outputs:** `data/interim/ios_layer1.jsonl`, `data/interim/ios_layer1_status.json`.

**Status:** not yet run (blocked on the shared 8B daily Groq budget refreshing enough headroom
after the Android run).

**How to run:**
```bash
./.venv/Scripts/python.exe -m phases.phase-4-layer1-broad.classify ios --batch 40
```

## Recall recovery (planned, not yet built)

Android's D12 finding — the 8B's `discovery` tag has ~96% recall but the ~4% it misses
concentrate almost entirely in the `ux`/`updates` piles — was validated by
`phases/phase-4-layer1-broad/recall_probe.py` (sampled) + `recover_discovery.py` (census of
`ux`+`updates`). Both scripts currently hardcode Android paths
(`data/interim/android_layer1.jsonl` → `android_discovery_pool.jsonl`).

For iOS, an equivalent `recover_discovery_ios.py` will census-check the iOS `ux`/`updates`
piles on the same 120B detector (independent Groq quota pool from the 8B, so this doesn't
compete with Layer-1 classification budget) and fold any missed discovery reviews into
`data/interim/ios_discovery_pool.jsonl` — the Phase 5 input. Will live in this folder once
built.

**Contract fields produced:** `funnel.substantiveCensus` (iOS uses the true census count, no
projection — see D14), category counts (exact, not ±MoE, since iOS is census not sample).
