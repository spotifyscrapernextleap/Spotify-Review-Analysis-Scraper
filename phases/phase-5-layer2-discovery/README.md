# Phase 5 — Layer-2: Deep Discovery Coding

**Objective:** open-code → consolidate codebook → closed-code the Android discovery
reviews into sub-themes with evidence snippets, populating the discovery deep-dive
contract fields.

**Inputs:** `data/interim/android_layer1.jsonl` (Phase 4) — the 2,359 reviews whose
multi-label `categories` include `discovery`.

**Steps:**
1. **Open-coding** (`open_code.py`, `gpt-oss-120b`) — 200 stratified reviews coded
   freely (no codebook) into short codes + verbatim snippets. → `phase5_opencode_raw.jsonl`,
   `phase5_opencode_codes.json` (105 unique codes).
2. **Codebook consolidation** — 105 codes → 11 sub-themes, mapped to contract groups
   (repetition/relevance/features/positive) + Bucket-2/3 + chosen/imposed bridge.
   → `codebook_DRAFT.md`. **🏷️ Human checkpoint: user sign-off before step 3.**
3. **Closed-coding** (not yet run) — tag all 2,359 against the locked codebook with
   snippets + abstention + `emerging`; extract use-contexts (behaviors) + needs/segments.

**Outputs / artifacts:** open-code sample + raw codes (done); draft codebook (done);
deep-coded records + theme/bucket/bridge tables (pending sign-off).

**Contract fields produced:** `discovery.*`, `buckets`, `bridge`, `behaviors`,
`unmetNeeds`, `segments`, `quotes`, `positiveDiscoveryThemes`, `funnel.deepCoded`,
`evaluation.abstention`.

**Model note:** `gpt-oss-120b` returns the answer in the content channel only with
`response_format=json_object` + a non-trivial prompt; `reasoning_effort="low"` keeps
completion tokens down. Its rate-limit pool is independent of the 8B Layer-1 pool.

**Status:** open-coding complete; **awaiting user sign-off on `codebook_DRAFT.md`**.

**How to re-run:**
```
./.venv/Scripts/python.exe -m phases.phase-5-layer2-discovery.open_code --batch 10
```
