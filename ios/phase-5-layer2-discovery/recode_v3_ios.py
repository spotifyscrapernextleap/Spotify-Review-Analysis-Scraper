"""Phase 5 (iOS) — v3 deep-code of the iOS discovery pool (gpt-oss-120b, codebook v3).

iOS analogue of phases/phase-5-layer2-discovery/recode_v3.py. Codes the iOS discovery
pool (built by ios/phase-4-layer1-broad/recover_discovery_ios.py) against codebook v3 on
the canonical model gpt-oss-120b, with the SAME three guardrails so non-discovery reviews
never enter the inventory:
  1. deterministic language guard  — non-English dropped BEFORE any model call;
  2. strict model discovery gate    — precision over recall;
  3. not_discovery records excluded — only discovery:true reaches the inventory.

NO-DRIFT DESIGN (see PROJECT_MEMORY.md D20): the codebook itself — the SYSTEM prompt, the
theme names/groups/buckets, the REMAP of retired codes, the guardrail helpers (`non_english`,
`_messages`, `_clean`, `_write`) — is IMPORTED from the Android recode_v3 module, not copied.
So both tracks code against a byte-identical rubric. Only iOS-specific I/O paths and the
`platform: "iOS"` quote label (and iOS's real per-storefront `country`, vs Android's "global")
live here.

Resumable: skips review_ids already in the coded log. Stops cleanly when the 120B daily
budget exhausts; re-run to finish the remainder.

Run:
  python -m ios.phase-5-layer2-discovery.recode_v3_ios [--batch 8] [--limit N]
  python -m ios.phase-5-layer2-discovery.recode_v3_ios --aggregate-only
Outputs:
  data/interim/ios_recode_v3_coded.jsonl    — per-review records (resume log)
  data/interim/ios_recode_v3_dropped.jsonl  — audit trail of dropped reviews
  data/interim/ios_recode_v3_analysis.json  — aggregated themes/bridge/buckets/etc.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict

from dotenv import load_dotenv

from common import config as C
from common.io import read_jsonl, write_json
from common.logging_setup import get_logger

sys.stdout.reconfigure(encoding="utf-8")
log = get_logger("ios.phase5.recode_v3")
load_dotenv(dotenv_path=str(C.ROOT / ".env"))

# ---- single-source the codebook + coding logic from the Android module -----
_spec = importlib.util.spec_from_file_location(
    "recode_v3_android",
    str(C.PHASES_DIR / "phase-5-layer2-discovery" / "recode_v3.py"))
av3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(av3)

# codebook constants (imported, NOT redefined — guarantees no drift vs Android)
NAMES = av3.NAMES
GROUP = av3.GROUP
BUCKET = av3.BUCKET
REPETITION = av3.REPETITION
THEME_IDS = av3.THEME_IDS
# coding helpers (imported): the strict discovery gate + theme cleaner + guards
non_english = av3.non_english
_messages = av3._messages
_clean = av3._clean
rp = av3.rp                       # recall_probe module (KeyPool / StopExhausted / _parse)

PLATFORM = "iOS"                  # Android hardcodes "Android"; iOS quotes are per-storefront
POOL = C.INTERIM_DIR / "ios_discovery_pool.jsonl"
CODED = C.INTERIM_DIR / "ios_recode_v3_coded.jsonl"
DROPPED = C.INTERIM_DIR / "ios_recode_v3_dropped.jsonl"
ANALYSIS = C.INTERIM_DIR / "ios_recode_v3_analysis.json"


def _write(fh, rec, c):
    fh.write(json.dumps({"review_id": rec["review_id"], "gid": rec.get("gid"),
                         "rating": rec.get("rating"), "country": rec.get("country"),
                         "date": rec.get("date"), "text": rec.get("text"),
                         "coder": C.GROQ_MODEL_DEEP, **c}, ensure_ascii=False) + "\n")
    fh.flush()


def run(batch_size, limit):
    keys = C.groq_api_keys()
    if not keys:
        raise SystemExit("No GROQ_API_KEY* in .env")
    if not POOL.exists():
        raise SystemExit(f"Missing {POOL} — run recover_discovery_ios.py first.")
    items = list(read_jsonl(POOL))
    if limit:
        items = items[:limit]
    done = {r["review_id"] for r in read_jsonl(CODED)} if CODED.exists() else set()
    todo = [r for r in items if r["review_id"] not in done]

    # GUARD 1 — deterministic language drop (no model call)
    lang_drop = [r for r in todo if non_english(r.get("text"))]
    to_model = [r for r in todo if r not in lang_drop]
    log.info("iOS v3 re-code: %d todo (%d done). language-dropped=%d, to-model=%d on %s batch=%d",
             len(todo), len(done), len(lang_drop), len(to_model), C.GROQ_MODEL_DEEP, batch_size)

    pool = rp.KeyPool(keys, model=C.GROQ_MODEL_DEEP)
    t0 = time.time(); n = 0; stopped = False
    rf = open(CODED, "a", encoding="utf-8")
    try:
        for r in lang_drop:
            _write(rf, r, {"discovery": False, "drop_reason": "language", "themes": [],
                           "repetition": None, "behavior": None, "unmet_need": None})
            n += 1
        for s in range(0, len(to_model), batch_size):
            batch = to_model[s:s + batch_size]
            est = sum(len(r.get("text") or "") for r in batch) // 3 + 1400
            try:
                # Shared fail-closed coder (imported from the Android module, no drift):
                # batch fail -> per-review retry -> explicit coding_failed DROP, never a
                # fabricated discovery verdict.
                coded = av3.code_or_fail(pool, batch, est)
            except rp.StopExhausted:
                log.warning("  ALL 120B keys exhausted at %d coded — stopping; resume when budget recovers", n)
                stopped = True
                break
            for rec, c in zip(batch, coded):
                _write(rf, rec, c)
                n += 1
            if (s // batch_size) % 10 == 0:
                log.info("  %d processed, tokens=%d, keys=%d", n, sum(pool.tokens), len(pool.healthy))
    finally:
        rf.close()
    if not stopped:
        aggregate()
    log.info("%s %.0fs tokens=%d processed=%d -> %s%s", "STOPPED" if stopped else "DONE",
             time.time() - t0, sum(pool.tokens), n, CODED.name,
             "  (resume to finish)" if stopped else "")


def aggregate():
    recs = list(read_jsonl(CODED))
    coded = [r for r in recs if r.get("discovery")]
    dropped = [r for r in recs if not r.get("discovery")]
    drop_reasons = Counter(r.get("drop_reason") for r in dropped)
    D = len(coded)

    # GUARD — real codings carry a verbatim snippet; the all-empty signature is what the
    # fail-OPEN bug produced (8 phantom 'emerging'). Loud + auditable, not a hard crash.
    suspect = [r["review_id"] for r in coded
               if r.get("themes") and all(not (t.get("snippet") or "") for t in r["themes"])]
    if suspect:
        log.error("GUARD: %d discovery records have ALL-EMPTY snippets (possible failed/fabricated "
                  "coding, review): %s", len(suspect), suspect[:15])

    with open(DROPPED, "w", encoding="utf-8") as fh:
        for r in dropped:
            fh.write(json.dumps({"review_id": r["review_id"], "reason": r.get("drop_reason"),
                                 "rating": r.get("rating"), "text": r.get("text")},
                                ensure_ascii=False) + "\n")

    theme_revs = defaultdict(list)
    for r in coded:
        for t in r["themes"]:
            theme_revs[t["theme"]].append(r)

    def avg_rating(rs):
        xs = [x["rating"] for x in rs if x.get("rating")]
        return round(sum(xs) / len(xs), 2) if xs else None

    themes = []
    for tid in list(NAMES) + (["emerging"] if theme_revs.get("emerging") else []):
        rs = theme_revs.get(tid, [])
        if not rs and tid != "emerging":
            continue
        themes.append({"id": tid, "name": NAMES.get(tid, "Other / emerging"),
                       "count": len(rs), "pct": round(100 * len(rs) / D, 1) if D else 0,
                       "sentiment": avg_rating(rs), "group": GROUP.get(tid, "features")})

    rep_recs = [r for r in coded if any(t["theme"] in REPETITION for t in r["themes"])]
    chosen = [r for r in rep_recs if r.get("repetition") == "chosen"]
    imposed = [r for r in rep_recs if r.get("repetition") == "imposed"]

    def items_for(rs):
        c = Counter()
        for r in rs:
            for t in r["themes"]:
                if t["theme"] in REPETITION:
                    c[NAMES[t["theme"]]] += 1
        return [{"name": k, "count": v} for k, v in c.most_common()]

    bk = {"finding": Counter(), "recs": Counter()}
    for r in coded:
        for t in r["themes"]:
            b = BUCKET.get(t["theme"])
            if b:
                bk[b][t["theme"]] += 1
    emerging_finding = sum(1 for r in coded if any(t["theme"] == "emerging" for t in r["themes"]))

    beh = Counter(r["behavior"] for r in coded if r.get("behavior"))
    seg_rating = defaultdict(list)
    for r in coded:
        if r.get("behavior"):
            seg_rating[r["behavior"]].append(r.get("rating"))
    segments = [{"name": b, "size": round(100 * k / D, 1),
                 "avgRating": round(sum(x for x in seg_rating[b] if x) / max(1, len([x for x in seg_rating[b] if x])), 2)
                 if [x for x in seg_rating[b] if x] else None, "mentions": k}
                for b, k in beh.most_common()]

    pos_aspects = Counter(t.get("aspect") for r in coded for t in r["themes"]
                          if t["theme"] == "love" and t.get("aspect"))
    needs = Counter(r["unmet_need"] for r in coded if r.get("unmet_need"))

    quotes = {}
    for tid, rs in theme_revs.items():
        qs = []
        for r in rs[:12]:
            snip = next((t["snippet"] for t in r["themes"] if t["theme"] == tid and t["snippet"]), r["text"])
            qs.append({"text": snip, "rating": r.get("rating"), "platform": PLATFORM,
                       "store": (r.get("country") or "").upper()})
        quotes[tid] = qs

    out = {
        "codebook": "v3", "track": "ios", "pool": len(recs), "deepCoded": D, "dropped": len(dropped),
        "dropReasons": dict(drop_reasons),
        "dropRate": round(100 * len(dropped) / len(recs), 1) if recs else 0,
        "avgRating": avg_rating(coded), "themes": themes,
        "repetitionCluster": {"themeIds": ["repeat", "shuffle"], "totalCount": len(rep_recs),
                              "pctOfDiscovery": round(100 * len(rep_recs) / D, 1) if D else 0},
        "bridge": {"total": len(rep_recs),
                   "chosen": {"total": len(chosen), "items": items_for(chosen)},
                   "imposed": {"total": len(imposed), "items": items_for(imposed)},
                   "unlabeled": len(rep_recs) - len(chosen) - len(imposed)},
        "buckets": {"finding": {"ids": list(bk["finding"]), "counts": dict(bk["finding"]),
                                "emerging": emerging_finding},
                    "recs": {"ids": list(bk["recs"]), "counts": dict(bk["recs"]), "emerging": 0}},
        "behaviors": [{"name": b, "mentions": k} for b, k in beh.most_common()],
        "segments": segments,
        "positiveDiscoveryThemes": [{"name": a, "count": c} for a, c in pos_aspects.most_common(8)],
        "unmetNeeds_raw": [{"need": nd, "mentions": c} for nd, c in needs.most_common(20)],
        "quotes": quotes,
    }
    write_json(ANALYSIS, out)
    print("\n========== iOS PHASE 5 v3 RE-CODE (gpt-oss-120b) ==========")
    print(f"pool={out['pool']}  discovery-kept={D}  dropped={len(dropped)} ({out['dropRate']}%)  "
          f"reasons={dict(drop_reasons)}")
    print(f"discovery avg rating={out['avgRating']}")
    print("\nthemes (count, pct, avg-rating, group):")
    for t in sorted(out["themes"], key=lambda x: -x["count"]):
        print(f"  {t['count']:4d}  {t['pct']:4.1f}%  r={t['sentiment']}  [{t['group']:10s}] {t['id']} — {t['name']}")
    br = out["bridge"]
    print(f"\nrepetition cluster (repeat+shuffle): {out['repetitionCluster']['totalCount']} "
          f"({out['repetitionCluster']['pctOfDiscovery']}% of discovery)")
    print(f"  bridge: chosen={br['chosen']['total']}  imposed={br['imposed']['total']}  unlabeled={br['unlabeled']}")
    # emerging-rate check: if v3 doesn't fit iOS, this spikes -> flag for the user
    emerging_ct = next((t["count"] for t in out["themes"] if t["id"] == "emerging"), 0)
    emerging_pct = round(100 * emerging_ct / D, 1) if D else 0
    print(f"\nemerging rate: {emerging_ct}/{D} = {emerging_pct}%  "
          f"({'⚠ HIGH — v3 fit for iOS is questionable, review before snapshot' if emerging_pct >= 15 else 'ok — v3 fits iOS'})")
    print(f"behaviors: {dict(beh)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--aggregate-only", action="store_true")
    a = p.parse_args()
    if a.aggregate_only:
        aggregate()
    else:
        run(a.batch, a.limit)
