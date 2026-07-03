"""Phase 5 — v3 FULL re-code of the discovery pool (gpt-oss-120b, codebook v3).

Re-codes the ENTIRE 1,792-review discovery pool (`phase5_recode_items.jsonl`) against
codebook v3 in one consistent pass on the canonical model gpt-oss-120b. v3 retires
`autoplay` and `safe`, and adds STRICT guardrails so non-discovery reviews never enter
the inventory:
  1. deterministic language guard  — non-English dropped BEFORE any model call;
  2. strict model discovery gate    — precision over recall;
  3. not_discovery records excluded — only discovery:true reaches the inventory.

Resumable: skips review_ids already in the coded log. Stops cleanly when the 120B
daily budget exhausts; just re-run to finish the remainder.

Run:
  python -m phases.phase-5-layer2-discovery.recode_v3 [--batch 8] [--limit N]
  python -m phases.phase-5-layer2-discovery.recode_v3 --aggregate-only
Outputs:
  data/interim/phase5_recode_v3_coded.jsonl    — per-review records (resume log)
  data/interim/phase5_recode_v3_dropped.jsonl  — audit trail of dropped reviews
  data/interim/phase5_recode_v3_analysis.json  — aggregated themes/bridge/buckets/etc.
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
log = get_logger("phase5.recode_v3")
load_dotenv(dotenv_path=str(C.ROOT / ".env"))

# reuse the deep-model KeyPool / parser / StopExhausted from the recall probe
_spec = importlib.util.spec_from_file_location(
    "recall_probe", str(C.PHASES_DIR / "phase-4-layer1-broad" / "recall_probe.py"))
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)

# ---- codebook v3 (autoplay + safe RETIRED) --------------------------------
NAMES = {
    "repeat": "Same songs on repeat", "shuffle": "Shuffle isn't random",
    "mismatch": "Irrelevant / wrong recs", "pushy": "Unwanted recs pushed",
    "smartrec": "Wants smarter / personalized recs",
    "control": "No control over recs", "freegate": "Free tier blocks discovery",
    "dj": "AI DJ problems", "newmusic": "Can't surface new releases",
    "love": "Discovery that delights",
}
GROUP = {"repeat": "repetition", "shuffle": "repetition", "mismatch": "relevance",
         "pushy": "relevance", "smartrec": "relevance", "control": "features",
         "freegate": "features", "dj": "features", "newmusic": "features", "love": "positive"}
BUCKET = {"control": "finding", "freegate": "finding", "dj": "finding", "newmusic": "finding",
          "mismatch": "recs", "pushy": "recs", "smartrec": "recs"}
REPETITION = {"repeat", "shuffle"}            # autoplay retired
THEME_IDS = set(NAMES)
# retired codes get remapped if the model emits them anyway
REMAP = {"autoplay": "control", "safe": "repeat"}
BEHAVIORS = {"workout", "focus_study", "sleep", "commute_driving",
             "background_chores", "party_social", "mood"}

SYSTEM = """You are deep-coding Spotify app-store reviews about MUSIC DISCOVERY / RECOMMENDATIONS / PLAYBACK CONTROL against a FIXED codebook (v3). For EACH numbered review do all of:

A) STRICT DISCOVERY GATE. Set "discovery": false (DROP the review) UNLESS it has a CLEAR, SUBSTANTIVE angle on at least one of: recommendations / Discover Weekly / Daily Mix / Release Radar / Wrapped-as-taste; the recommendation algorithm or taste-matching; smart shuffle / AI DJ / autoplay CHOOSING what plays; shuffle not being random; songs repeating / limited rotation / stale recs; finding or surfacing NEW music; wanting CONTROL over what is recommended or what plays (can't pick songs, forced playback); or FREE-TIER limits that block choosing music (shuffle-only, skip/selection limits).
Set "discovery": false when the review is ONLY about, with no real discovery angle: ads / price / subscription cost (and NOT about being forced to shuffle/can't pick); a crash / bug / login / offline / device (car/Bluetooth) error; sound or audio quality; a specific song or artist simply MISSING from the catalogue; podcasts / audiobooks; or generic praise / insult with no mention of recommendations or what plays. When genuinely unsure, or the discovery angle is a single passing word with no substance, set "discovery": false. PRECISION OVER RECALL — a clean discovery inventory matters more than catching every borderline case.

B) THEMES (only if discovery:true). Assign 1-3 codes (most reviews ONE), closest first:
- repeat: same songs on repeat, limited rotation, "plays the same stuff", recs feel stale/repetitive
- shuffle: shuffle isn't random / forced shuffle / "shuffle only"
- mismatch: irrelevant or wrong recommendations / wrong genre / unrelated suggestions
- pushy: unwanted recommendations forced at you / AI recs dominate / pushed content
- smartrec: a CONSTRUCTIVE request for smarter / more personalized recs or a discovery feature
- control: wants control over what plays or is recommended / can't pick songs / queue or autoplay plays songs you didn't choose / wants to disable a feature
- freegate: the FREE tier blocks discovery (shuffle-only, skip/selection limits gate choosing music)
- dj: AI DJ specifically (cuts songs, crashes, poor picks, missing, or praised)
- newmusic: can't find/surface NEW releases / Release Radar broken / refresh broken
- love: POSITIVE discovery experience (Discover Weekly / Daily Mix / Wrapped / "finds anything" praise)
If genuinely discovery but fits none, use "emerging" (use sparingly).

IMPORTANT — two codes were REMOVED in v3; NEVER output "autoplay" or "safe". Instead:
- a queue/autoplay that won't stop or plays songs you didn't choose -> "control" (add "repeat" if it's the SAME songs); if it is purely an app malfunction/glitch with no discovery angle -> discovery:false.
- recs too safe / too similar / stale / filter-bubble -> "repeat" if the same songs recur; "newmusic" if it's about no NEW releases; "mismatch" if the recs are wrong; "smartrec" if they ask for better recs.

Give each theme a VERBATIM snippet (exact substring from the review). For "love", also set "aspect" to the praised feature (e.g. "Discover Weekly", "Smart Shuffle", "Wrapped", "Finds anything").

C) REPETITION TYPE — REQUIRED whenever you tag a repeat or shuffle theme (otherwise null). You MUST choose one, never null: "imposed" (the APP forces sameness/shuffle/repetition against the user's wish — this is the DEFAULT, true for almost all repetition complaints) or "chosen" (the USER explicitly wants to replay the same music for comfort/mood/habit). If a repeat/shuffle theme is present, do not leave this null.

D) BEHAVIOR (the listening context the review discloses, else null): one of workout, focus_study, sleep, commute_driving, background_chores, party_social, mood.

E) UNMET_NEED: a short (<=6 word) phrase naming what the user wishes existed, else null.

Return ONLY JSON: {"results":[{"i":1,"discovery":true,"themes":[{"theme":"control","snippet":"won't let me pick my own songs","aspect":null}],"repetition":null,"behavior":null,"unmet_need":"let me pick songs"}, ...]} — exactly one object per input review, preserving numbering."""


# ---- deterministic language guard -----------------------------------------
def _init_langdetect():
    try:
        from langdetect import detect_langs, DetectorFactory
        DetectorFactory.seed = 0
        return detect_langs
    except Exception:  # noqa: BLE001
        return None


_detect_langs = _init_langdetect()


def non_english(text):
    """Strict guard for the deep pool (stricter than Phase-2's lenient filter).
    Only flags reviews long enough to judge confidently — short texts are kept and
    left to the model gate."""
    t = (text or "").strip()
    if len(t) < 60 or _detect_langs is None:
        return False
    try:
        top = _detect_langs(t)[0]
        return top.lang != "en" and top.prob >= 0.90
    except Exception:  # noqa: BLE001
        return False


def _messages(batch):
    lines = [f"{i+1}. {(r.get('text') or '').strip()}" for i, r in enumerate(batch)]
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Reviews:\n" + "\n".join(lines)}]


def _clean(lab):
    if not lab.get("discovery"):
        return {"discovery": False, "drop_reason": "not_discovery",
                "themes": [], "repetition": None, "behavior": None, "unmet_need": None}
    themes = []
    for t in (lab.get("themes") or [])[:3]:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("theme", "")).strip().lower()
        tid = REMAP.get(tid, tid)                      # fold any stray autoplay/safe
        if tid in THEME_IDS or tid == "emerging":
            if any(x["theme"] == tid for x in themes):
                continue
            themes.append({"theme": tid, "snippet": (t.get("snippet") or "").strip(),
                           "aspect": (t.get("aspect") or None) if tid == "love" else None})
    if not themes:                                     # discovery:true but no usable theme
        themes = [{"theme": "emerging", "snippet": "", "aspect": None}]
    rep = lab.get("repetition") if lab.get("repetition") in ("chosen", "imposed") else None
    if not any(t["theme"] in REPETITION for t in themes):
        rep = None
    beh = lab.get("behavior") if lab.get("behavior") in BEHAVIORS else None
    need = (lab.get("unmet_need") or "").strip() or None
    return {"discovery": True, "drop_reason": None,
            "themes": themes, "repetition": rep, "behavior": beh, "unmet_need": need}


def _write(fh, rec, c):
    fh.write(json.dumps({"review_id": rec["review_id"], "gid": rec.get("gid"),
                         "rating": rec.get("rating"), "country": rec.get("country"),
                         "date": rec.get("date"), "text": rec.get("text"),
                         "coder": C.GROQ_MODEL_DEEP, **c}, ensure_ascii=False) + "\n")
    fh.flush()


def code_or_fail(pool, batch, est):
    """Code a batch, FAIL-CLOSED. Try the batch up to 3x; if it will not parse, retry
    each review on its own (single-item JSON is far more robust than a big batch that
    truncates mid-array). Any review that STILL will not parse is DROPPED with
    drop_reason='coding_failed' — it is NEVER fabricated as a discovery verdict. Returns
    a list of cleaned records aligned to `batch`. Propagates StopExhausted so the caller
    can stop and resume.

    This is the pipeline-wide fail-closed policy: a coding failure must remove a review
    from the inventory and leave an auditable marker, not invent a label (the fail-OPEN
    bug that put 8 uncoded reviews into iOS as bogus 'emerging').
    """
    for _try in range(3):
        resp = pool.complete(_messages(batch), est)
        parsed = rp._parse(resp.choices[0].message.content, len(batch)) if resp else None
        if parsed is not None:
            return [_clean(lab) for lab in parsed]
    log.warning("  batch of %d failed to parse 3x — retrying per-review (fail-closed)", len(batch))
    out = []
    for one in batch:
        one_est = len(one.get("text") or "") // 3 + 900
        one_parsed = None
        for _t in range(2):
            resp = pool.complete(_messages([one]), one_est)
            one_parsed = rp._parse(resp.choices[0].message.content, 1) if resp else None
            if one_parsed:
                break
        if one_parsed:
            out.append(_clean(one_parsed[0]))
        else:
            log.error("  REVIEW %s uncodeable after per-review retry — DROP (coding_failed)",
                      one.get("review_id"))
            out.append({"discovery": False, "drop_reason": "coding_failed", "themes": [],
                        "repetition": None, "behavior": None, "unmet_need": None})
    return out


def run(batch_size, limit):
    keys = C.groq_api_keys()
    if not keys:
        raise SystemExit("No GROQ_API_KEY* in .env")
    items = list(read_jsonl(C.INTERIM_DIR / "phase5_recode_items.jsonl"))
    if limit:
        items = items[:limit]
    rec_path = C.INTERIM_DIR / "phase5_recode_v3_coded.jsonl"
    done = {r["review_id"] for r in read_jsonl(rec_path)} if rec_path.exists() else set()
    todo = [r for r in items if r["review_id"] not in done]

    # GUARD 1 — deterministic language drop (no model call)
    lang_drop = [r for r in todo if non_english(r.get("text"))]
    to_model = [r for r in todo if r not in lang_drop]
    log.info("v3 re-code: %d todo (%d already done). language-dropped=%d, to-model=%d on %s batch=%d",
             len(todo), len(done), len(lang_drop), len(to_model), C.GROQ_MODEL_DEEP, batch_size)

    pool = rp.KeyPool(keys, model=C.GROQ_MODEL_DEEP)
    t0 = time.time(); n = 0; stopped = False
    rf = open(rec_path, "a", encoding="utf-8")
    try:
        for r in lang_drop:
            _write(rf, r, {"discovery": False, "drop_reason": "language", "themes": [],
                           "repetition": None, "behavior": None, "unmet_need": None})
            n += 1
        for s in range(0, len(to_model), batch_size):
            batch = to_model[s:s + batch_size]
            est = sum(len(r.get("text") or "") for r in batch) // 3 + 1400
            try:
                coded = code_or_fail(pool, batch, est)
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
             time.time() - t0, sum(pool.tokens), n, rec_path.name,
             "  (resume to finish)" if stopped else "")


def aggregate():
    recs = list(read_jsonl(C.INTERIM_DIR / "phase5_recode_v3_coded.jsonl"))
    coded = [r for r in recs if r.get("discovery")]
    dropped = [r for r in recs if not r.get("discovery")]
    drop_reasons = Counter(r.get("drop_reason") for r in dropped)
    D = len(coded)

    # GUARD — surface any inventory record whose themes ALL lack a snippet. Real codings
    # carry a verbatim snippet; the all-empty signature is what the fail-OPEN bug produced.
    # Loud + auditable (feeds the coded/failed report) rather than a hard crash.
    suspect = [r["review_id"] for r in coded
               if r.get("themes") and all(not (t.get("snippet") or "") for t in r["themes"])]
    if suspect:
        log.error("GUARD: %d discovery records have ALL-EMPTY snippets (possible failed/fabricated "
                  "coding, review): %s", len(suspect), suspect[:15])

    # audit trail of every dropped review
    with open(C.INTERIM_DIR / "phase5_recode_v3_dropped.jsonl", "w", encoding="utf-8") as fh:
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
            qs.append({"text": snip, "rating": r.get("rating"), "platform": "Android",
                       "store": (r.get("country") or "global").upper()})
        quotes[tid] = qs

    out = {
        "codebook": "v3", "pool": len(recs), "deepCoded": D, "dropped": len(dropped),
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
    write_json(C.INTERIM_DIR / "phase5_recode_v3_analysis.json", out)
    print("\n========== PHASE 5 v3 RE-CODE (gpt-oss-120b) ==========")
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
