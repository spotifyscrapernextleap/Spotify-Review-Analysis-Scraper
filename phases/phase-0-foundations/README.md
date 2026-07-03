# Phase 0 — Foundations & Scaffolding

**Objective:** make the repo runnable and make the data contract *enforceable in code* before any data exists.

**Inputs:** the binding specs in `build and design docs/` (Data Contract in `README.md`; mock `source/data.js`).

**Steps:**
1. Created the Python virtualenv (`.venv/`) and installed pipeline deps (`requirements.txt`).
2. Built the shared `common/` package:
   - `config.py` — all build parameters (app ids, countries, ~12-month net, filter thresholds, taxonomy, Groq models). **Re-target the tool by editing this one file.**
   - `contract.py` — pydantic models that mirror `window.REVIEW_DATA` exactly, plus `cross_checks()` for the consistency rules types can't catch (funnel reconcile, bucket→theme id integrity, baseline sum, quote keys).
   - `io.py`, `logging_setup.py` — shared helpers.
3. Authored the **golden filter set** (`golden_set.jsonl`, 27 worked examples): clear keeps, clear junk, and the named borderlines — short-but-substantive, long-but-empty — plus Hinglish/slang probes and a near-dupe pair. This both tunes and tests Phase 2.

**Outputs / artifacts:**
- `common/` package (importable across phases).
- `phases/phase-0-foundations/golden_set.jsonl` — filter ground truth.
- `phases/phase-0-foundations/mock_to_json.js` — converts the prototype `data.js` to JSON for validation.
- `data/interim/mock_review_data.json` — the prototype contract as JSON.
- `requirements.txt`, `.env.example`, `.gitignore`.

**Contract fields produced:** none yet — this phase encodes the *schema*, not data.

**Tests run:**
- **Contract self-test (Phase 0 exit gate):** converted the real prototype `data.js` → JSON and validated it against `common/contract.py`. Result: ✅ *validates and passes cross-checks*. This proves the schema I encoded accepts the real contract shape — so when Phase 7 emits, a pass means the dashboard will render (EC-26).

**Exit criteria:** ✅ contract models validate the mock; golden set loads; deps import (incl. `google-play-scraper`, `app-store-scraper`).

**Checkpoints / human input:** none. (Groq key not needed until Phase 4.)

**How to re-run:**
```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
node "phases/phase-0-foundations/mock_to_json.js" > data/interim/mock_review_data.json
./.venv/Scripts/python.exe -m common.contract data/interim/mock_review_data.json
```
