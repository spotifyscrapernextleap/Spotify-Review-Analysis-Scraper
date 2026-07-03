# Phase 5 — Layer-2: Deep Discovery Coding (iOS track)

**Objective:** tag every iOS discovery review against **codebook v3**
(`phases/phase-5-layer2-discovery/codebook_v3_REVISED.md` — the current, canonical codebook;
`autoplay` and `safe` are retired, 10 live themes) — the same codebook Android's final
deep-dive uses, so the two tracks' discovery sub-theme numbers are directly comparable even
though they're never merged into one blended figure.

**Codebook is shared by reference, not copied:** `codebook_v3_REVISED.md` lives once, under
`phases/phase-5-layer2-discovery/`. Forking a copy here would risk the two tracks silently
coding against different rubrics.

**Inputs:** `data/interim/ios_discovery_pool.jsonl` (Phase 4 recovery output — iOS discovery
census + any recovered `ux`/`updates` misses).

**Model:** `gpt-oss-120b` (the canonical model for any v3-codebook run per D16 — Claude
hand-coding was only used for the Android v2 pass under a since-superseded deadline
constraint).

**Guardrails (same three as Android's `recode_v3.py`, D16):**
1. deterministic langdetect drop before any model call;
2. strict in-prompt discovery gate (precision over recall);
3. `not_discovery` verdicts excluded from the inventory.

**Status:** not yet built. Will be `recode_v3_ios.py` — a track-adapted copy of
`phases/phase-5-layer2-discovery/recode_v3.py` with iOS paths and `platform: "iOS"` /
real per-storefront `country` on quotes (unlike Android, where `country` was relabelled
`"global"` — iOS countries are genuine, see Phase 2 D4).

**Outputs (planned):** `data/interim/ios_recode_v3_{coded,dropped}.jsonl`,
`data/interim/ios_recode_v3_analysis.json`.

**Contract fields produced:** `discovery.*`, `buckets`, `bridge`, `behaviors`, `unmetNeeds`,
`segments`, `quotes`, `positiveDiscoveryThemes` — the iOS analogues of the Android v3 fields.

**How to run (once built):**
```bash
./.venv/Scripts/python.exe -m ios.phase-5-layer2-discovery.recode_v3_ios [--batch 8]
```
