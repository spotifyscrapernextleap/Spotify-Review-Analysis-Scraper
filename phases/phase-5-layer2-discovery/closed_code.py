"""Phase 5 — Layer-2 deep Discovery coding: CLOSED-CODING pass (gpt-oss-120b).

Step 3 of Phase 5. Tags every review in the locked discovery pool
(`android_discovery_pool.jsonl`, 2,495) against the SIGNED-OFF 11-theme codebook:
1-2 sub-themes + verbatim snippet each; a chosen/imposed label for repetition
themes (the bridge); a disclosed use-context (Bucket 1 / segments); and an
abstention flag (`discovery:false`) that drops 8B false-positives.

Resumable: skips review_ids already in the records file.

Run:
  python -m phases.phase-5-layer2-discovery.closed_code [--batch 8] [--limit N]
Outputs:
  data/interim/phase5_discovery_coded.jsonl   — per-review coded records (resume log)
  data/interim/phase5_discovery_analysis.json — aggregated themes/buckets/bridge/etc.
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
log = get_logger("phase5.closedcode")
load_dotenv(dotenv_path=str(C.ROOT / ".env"))

# Reuse the deep-model KeyPool from the recall probe.
_spec = importlib.util.spec_from_file_location(
    "recall_probe", str(C.PHASES_DIR / "phase-4-layer1-broad" / "recall_probe.py"))
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)

# ---- the signed-off codebook ----------------------------------------------
NAMES = {
    "repeat": "Same songs on repeat", "shuffle": "Shuffle isn't random",
    "autoplay": "Autoplay forces songs", "safe": "Recs too safe / filter bubble",
    "mismatch": "Irrelevant / wrong recs", "pushy": "Unwanted recs pushed",
    "control": "No control over recs", "freegate": "Free tier blocks discovery",
    "dj": "AI DJ problems", "newmusic": "Can't surface new releases",
    "love": "Discovery that delights",
}
GROUP = {"repeat": "repetition", "shuffle": "repetition", "autoplay": "repetition",
         "safe": "relevance", "mismatch": "relevance", "pushy": "relevance",
         "control": "features", "freegate": "features", "dj": "features",
         "newmusic": "features", "love": "positive"}
BUCKET = {"control": "finding", "freegate": "finding", "dj": "finding", "newmusic": "finding",
          "safe": "recs", "mismatch": "recs", "pushy": "recs"}
REPETITION = {"repeat", "shuffle", "autoplay"}
THEME_IDS = set(NAMES)
BEHAVIORS = {"workout", "focus_study", "sleep", "commute_driving",
             "background_chores", "party_social", "mood"}

SYSTEM = """You are deep-coding Spotify reviews that are about MUSIC DISCOVERY / RECOMMENDATIONS, against a FIXED codebook. For EACH numbered review do all of:

A) DISCOVERY CHECK. DEFAULT to "discovery": true. A review IS discovery if it has ANY angle — even secondary — on: recommendations; Discover Weekly / Daily Mix / Wrapped; the algorithm or taste-matching; smart shuffle / autoplay / AI DJ choosing what plays; shuffle randomness; repetition / "same songs"; finding or searching for music ("can find anything", "can't find new music"); wanting control over what is recommended or what plays; or free-tier shuffle/skip/selection limits that block choosing music. Set "discovery": false ONLY when the review is PURELY about something else with ZERO discovery angle (only ads/price/billing; only a crash/bug/login error; only sound quality; only a specific missing song; or only generic praise/insult with no mention of recommendations or what plays). When unsure, prefer true and pick the closest theme.

B) THEMES. Assign 1-2 codes from this fixed list (use the closest; most reviews are ONE):
- repeat: same songs on repeat, limited rotation, "plays the same stuff"
- shuffle: shuffle isn't random / forced shuffle / "shuffle only"
- autoplay: autoplay or auto-pick won't stop / switches to songs you didn't choose
- safe: recommendations too safe / too similar / stuck / filter bubble / not enough new
- mismatch: irrelevant or wrong recommendations / wrong genre / unrelated suggestions
- pushy: unwanted recommendations forced at you / AI recs dominate / pushed content
- control: wants control over recs/playback / can't pick songs / wants to disable a feature
- freegate: the FREE tier blocks discovery (shuffle-only, skip/selection limits gate it)
- dj: AI DJ specifically (cuts songs, crashes, poor picks, missing, praised)
- newmusic: can't find/surface NEW releases / Release Radar broken / refresh broken
- love: POSITIVE discovery experience (Discover Weekly/Daily Mix/Wrapped/"finds anything" praise)
If it's genuinely discovery but fits none, use "emerging".
Give each theme a VERBATIM snippet (exact substring). For "love", also set "aspect" to the praised feature (e.g. "Discover Weekly", "Smart Shuffle", "Wrapped", "Finds anything").

C) REPETITION TYPE (only if a repeat/shuffle/autoplay theme is present, else null):
- "chosen": the USER wants to replay the same music (comfort, mood, habit, intentional).
- "imposed": the APP forces sameness/shuffle/bad autoplay against the user's wish.

D) BEHAVIOR (the listening context the review discloses, else null): one of workout, focus_study, sleep, commute_driving, background_chores, party_social, mood.

E) UNMET_NEED: a short (<=6 word) phrase naming what the user wishes existed, else null.

Return ONLY JSON: {"results":[{"i":1,"discovery":true,"themes":[{"theme":"shuffle","snippet":"forced shuffle ruins it","aspect":null}],"repetition":"imposed","behavior":"commute_driving","unmet_need":"turn off forced shuffle"}, ...]} — exactly one object per input review, preserving numbering."""


def _messages(batch):
    lines = [f"{i+1}. {(r.get('text') or '').strip()}" for i, r in enumerate(batch)]
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Reviews:\n" + "\n".join(lines)}]


def _clean(lab):
    if not lab.get("discovery"):
        return {"discovery": False, "themes": [], "repetition": None, "behavior": None, "unmet_need": None}
    themes = []
    for t in (lab.get("themes") or [])[:2]:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("theme", "")).strip().lower()
        if tid in THEME_IDS or tid == "emerging":
            themes.append({"theme": tid, "snippet": (t.get("snippet") or "").strip(),
                           "aspect": (t.get("aspect") or None) if tid == "love" else None})
    rep = lab.get("repetition") if lab.get("repetition") in ("chosen", "imposed") else None
    beh = lab.get("behavior") if lab.get("behavior") in BEHAVIORS else None
    need = (lab.get("unmet_need") or "").strip() or None
    return {"discovery": True, "themes": themes, "repetition": rep, "behavior": beh, "unmet_need": need}


def run(batch_size, limit, model, input_path=None, output_path=None, coder=None):
    keys = C.groq_api_keys()
    if not keys:
        raise SystemExit("No GROQ_API_KEY* in .env")
    input_path = input_path or (C.INTERIM_DIR / "android_discovery_pool.jsonl")
    pool_reviews = list(read_jsonl(input_path))
    if limit:
        pool_reviews = pool_reviews[:limit]
    rec_path = output_path or (C.INTERIM_DIR / "phase5_discovery_coded.jsonl")
    done = {r["review_id"] for r in read_jsonl(rec_path)} if rec_path.exists() else set()
    todo = [r for r in pool_reviews if r["review_id"] not in done]
    log.info("closed-coding %d reviews (%d done) on %s, batch=%d",
             len(todo), len(done), model, batch_size)

    pool = rp.KeyPool(keys, model=model)
    t0 = time.time(); n = 0; stopped = False
    rf = open(rec_path, "a", encoding="utf-8")
    try:
        for s in range(0, len(todo), batch_size):
            batch = todo[s:s + batch_size]
            est = sum(len(r.get("text") or "") for r in batch) // 3 + 1200
            parsed = None
            try:
                for _try in range(3):
                    resp = pool.complete(_messages(batch), est)
                    parsed = rp._parse(resp.choices[0].message.content, len(batch)) if resp else None
                    if parsed is not None:
                        break
            except rp.StopExhausted:
                log.warning("  ALL 120B keys exhausted at %d/%d — stopping; resume when budget recovers",
                            n, len(todo))
                stopped = True
                break
            if parsed is None:
                parsed = [{"discovery": True, "themes": [{"theme": "emerging", "snippet": ""}]}] * len(batch)
            for rec, lab in zip(batch, parsed):
                c = _clean(lab)
                rf.write(json.dumps({"review_id": rec["review_id"], "rating": rec.get("rating"),
                                     "country": rec.get("country"), "date": rec.get("date"),
                                     "source": rec.get("discovery_source"), "text": rec.get("text"),
                                     "coder": coder or model, **c}, ensure_ascii=False) + "\n")
                rf.flush(); n += 1
            if (s // batch_size) % 10 == 0:
                log.info("  %d/%d coded, tokens=%d, keys=%d", n, len(todo), sum(pool.tokens), len(pool.healthy))
    finally:
        rf.close()
    total = len(list(read_jsonl(rec_path)))
    is_canonical = rec_path == (C.INTERIM_DIR / "phase5_discovery_coded.jsonl")
    if is_canonical:
        aggregate()
    log.info("%s %.0fs tokens=%d  coded=%d/%d -> %s%s", "STOPPED" if stopped else "DONE",
             time.time() - t0, sum(pool.tokens), total, len(pool_reviews), rec_path.name,
             "  (resume to finish remainder)" if stopped else "")


def build_companion_input():
    """Companion input = reviews the 120B canonical run DROPPED (discovery:false)
    + reviews it never reached (uncoded). These get re-checked by the 20B companion."""
    pool = {r["review_id"]: r for r in read_jsonl(C.INTERIM_DIR / "android_discovery_pool.jsonl")}
    canon = list(read_jsonl(C.INTERIM_DIR / "phase5_discovery_coded.120b.jsonl"))
    coded_ids = {r["review_id"] for r in canon}
    dropped_ids = {r["review_id"] for r in canon if not r.get("discovery")}
    uncoded_ids = [rid for rid in pool if rid not in coded_ids]
    target_ids = list(dropped_ids) + uncoded_ids
    out = C.INTERIM_DIR / "phase5_companion_input.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for rid in target_ids:
            fh.write(json.dumps(pool[rid], ensure_ascii=False) + "\n")
    print(f"companion input: {len(dropped_ids)} dropped + {len(uncoded_ids)} uncoded = {len(target_ids)} -> {out.name}")
    return out


def merge_runs():
    """Final canonical set = 120B-kept discovery reviews (untouched) + any reviews
    the 20B companion RECOVERED as discovery from the dropped/uncoded pile. The 120B
    remains primary; the 20B only adds recovered discovery reviews."""
    canon = list(read_jsonl(C.INTERIM_DIR / "phase5_discovery_coded.120b.jsonl"))
    comp_path = C.INTERIM_DIR / "phase5_companion_coded.jsonl"
    comp = list(read_jsonl(comp_path)) if comp_path.exists() else []
    kept = [r for r in canon if r.get("discovery")]            # 120B-confirmed discovery
    kept_ids = {r["review_id"] for r in kept}
    recovered = [r for r in comp if r.get("discovery") and r["review_id"] not in kept_ids]
    dropped_final = ([r for r in canon if not r.get("discovery")
                      and r["review_id"] not in {x["review_id"] for x in recovered}])
    for r in kept:
        r.setdefault("coder", C.GROQ_MODEL_DEEP)
    merged = kept + recovered
    out = C.INTERIM_DIR / "phase5_discovery_coded.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for r in merged:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nMERGE: 120B-kept={len(kept)}  +  20B-recovered={len(recovered)}  =  {len(merged)} discovery")
    print(f"  companion checked {len(comp)} dropped/uncoded -> recovered {len(recovered)} "
          f"({100*len(recovered)/len(comp):.0f}%); {len(comp)-len(recovered)} confirmed non-discovery")
    aggregate()


def aggregate():
    recs = list(read_jsonl(C.INTERIM_DIR / "phase5_discovery_coded.jsonl"))
    coded = [r for r in recs if r.get("discovery")]
    abstained = [r for r in recs if not r.get("discovery")]
    D = len(coded)

    theme_revs = defaultdict(list)  # theme -> [rec]
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

    # repetition cluster + bridge
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

    # buckets
    bk = {"finding": Counter(), "recs": Counter()}
    for r in coded:
        for t in r["themes"]:
            b = BUCKET.get(t["theme"])
            if b:
                bk[b][t["theme"]] += 1
    emerging_finding = sum(1 for r in coded if any(t["theme"] == "emerging" for t in r["themes"]))

    # behaviors + segments
    beh = Counter(r["behavior"] for r in coded if r.get("behavior"))
    seg_rating = defaultdict(list)
    for r in coded:
        if r.get("behavior"):
            seg_rating[r["behavior"]].append(r.get("rating"))
    segments = []
    for b, k in beh.most_common():
        rts = [x for x in seg_rating[b] if x]
        segments.append({"name": b, "size": round(100 * k / D, 1),
                         "avgRating": round(sum(rts) / len(rts), 2) if rts else None, "mentions": k})

    # positive aspects + unmet needs
    pos_aspects = Counter(t.get("aspect") for r in coded for t in r["themes"]
                          if t["theme"] == "love" and t.get("aspect"))
    needs = Counter(r["unmet_need"] for r in coded if r.get("unmet_need"))

    # quotes by theme (up to 12 each)
    quotes = {}
    for tid, rs in theme_revs.items():
        qs = []
        for r in rs[:12]:
            snip = next((t["snippet"] for t in r["themes"] if t["theme"] == tid and t["snippet"]), r["text"])
            qs.append({"text": snip, "rating": r.get("rating"), "platform": "Android",
                       "store": (r.get("country") or "global").upper()})
        quotes[tid] = qs

    out = {
        "pool": len(recs), "deepCoded": D, "abstained": len(abstained),
        "abstainRate": round(100 * len(abstained) / len(recs), 1) if recs else 0,
        "avgRating": avg_rating(coded),
        "themes": themes,
        "repetitionCluster": {"themeIds": ["repeat", "shuffle", "autoplay"],
                              "totalCount": len(rep_recs),
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
        "recovered_in_pool": sum(1 for r in recs if r.get("source") == "recovered"),
    }
    write_json(C.INTERIM_DIR / "phase5_discovery_analysis.json", out)
    print("\n========== PHASE 5 CLOSED-CODING ==========")
    print(f"pool={out['pool']}  deep-coded(discovery)={D}  abstained(FP)={len(abstained)} ({out['abstainRate']}%)")
    print(f"discovery avg rating={out['avgRating']}")
    print("\nthemes (count, avg-rating, group):")
    for t in sorted(out["themes"], key=lambda x: -x["count"]):
        print(f"  {t['count']:4d}  {t['pct']:4.1f}%  r={t['sentiment']}  [{t['group']:10s}] {t['id']} — {t['name']}")
    rc = out["repetitionCluster"]; br = out["bridge"]
    print(f"\nrepetition cluster: {rc['totalCount']} ({rc['pctOfDiscovery']}% of discovery)")
    print(f"  bridge: chosen={br['chosen']['total']}  imposed={br['imposed']['total']}  unlabeled={br['unlabeled']}")
    print(f"buckets.finding ids={list(bk['finding'])} emerging={emerging_finding}")
    print(f"buckets.recs    ids={list(bk['recs'])}")
    print(f"behaviors: {dict(beh)}")
    print(f"top positive aspects: {dict(pos_aspects.most_common(6))}")
    print(f"top unmet needs: {[nd for nd,_ in needs.most_common(8)]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--model", default=C.GROQ_MODEL_DEEP,
                   help="deep model id; use C.GROQ_MODEL_DEEP_FAST (gpt-oss-20b) for the fast pool")
    p.add_argument("--input", default=None)
    p.add_argument("--output", default=None)
    p.add_argument("--coder", default=None, help="label stored on each record, e.g. '20b-companion'")
    p.add_argument("--aggregate-only", action="store_true")
    p.add_argument("--build-companion-input", action="store_true")
    p.add_argument("--merge", action="store_true")
    a = p.parse_args()
    if a.aggregate_only:
        aggregate()
    elif a.build_companion_input:
        build_companion_input()
    elif a.merge:
        merge_runs()
    else:
        inp = a.input and __import__("pathlib").Path(a.input)
        outp = a.output and __import__("pathlib").Path(a.output)
        run(a.batch, a.limit, a.model, input_path=inp, output_path=outp, coder=a.coder)
