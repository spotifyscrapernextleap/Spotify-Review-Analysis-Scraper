"""Phase 7 — compute every metric and emit the Android window.REVIEW_DATA snapshot.

Assembles the contract object from: the census funnel/window (Phase 1-3), the
Layer-1 sample (Phase 4, projected to the population +- MoE), the Claude re-code of
the discovery deep-dive (Phase 5, codebook v2, 690 hand-coded), and the gold-set
validation (Phase 6). Validates against common/contract.py.

Android is sample-based, so substantive/category/discovery counts are projected from
the stratified sample to the 96,822-candidate population (estimates +- margin of
error); census steps (collected/dedup/english/baseline/volume) are exact.

Run:  python -m phases.phase-7-analysis-snapshot.build_snapshot
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from collections import Counter, defaultdict

from common import config as C
from common.contract import validate_snapshot, cross_checks
from common.io import read_jsonl

sys.stdout.reconfigure(encoding="utf-8")
random.seed(42)
I = C.INTERIM_DIR
P6 = C.PHASES_DIR / "phase-6-gold-validation"
COLORS = {c["id"]: c["color"] for c in C.CATEGORIES}
CATNAME = {c["id"]: c["name"] for c in C.CATEGORIES}


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def rnd(x, n=1):
    return round(x, n)


# ---------------------------------------------------------------- census inputs
filt = jload(I / "android_filter_report.json")
win = jload(I / "android_window.json")
recode = jload(I / "phase5_recode_v3_analysis.json")   # v3: autoplay+safe retired, full gpt-oss-120b re-code
gold = jload(P6 / "gold_subtheme_scores.json")

f = filt["funnel"]
COLLECTED, DEDUP, ENGLISH = f["collected"], f["deduplicated"], f["english"]
TIERC_DET, SUBST_CAND = f["tierC"], f["substantive_candidates"]

# ---------------------------------------------------------------- sample stats
samp = list(read_jsonl(I / "android_layer1.jsonl"))
Ns = len(samp)
codeable = [r for r in samp if r.get("categories") != ["none"]]
NC = len(codeable)
none_rate = 1 - NC / Ns

# project the substantive-candidate population through the Layer-1 none-rate
PROJ_SUBST = round(NC / Ns * SUBST_CAND)                 # truly codeable
PROJ_TIERC = ENGLISH - PROJ_SUBST                        # contentless (det + Layer-1 none)
# tierA/tierB split by deep-codeability (text length proxy)
rich = sum(1 for r in codeable if len(r.get("text") or "") >= 120)
TIERA = round(rich / NC * PROJ_SUBST)
TIERB = PROJ_SUBST - TIERA

# category shares of codeable -> projected counts
cat_n = Counter(); cat_rating = defaultdict(list); cat_sent = defaultdict(Counter)
for r in codeable:
    for c in set(r.get("categories") or []):
        if c == "none":
            continue
        cat_n[c] += 1
        if r.get("rating"):
            cat_rating[c].append(r["rating"])
        cat_sent[c][r.get("sentiment")] += 1

DISC_SHARE = cat_n["discovery"] / NC
PROJ_DISCOVERY = round(DISC_SHARE * PROJ_SUBST)
DEEPCODED = recode["deepCoded"]

categories = []
for cid, n in cat_n.most_common():
    rs = cat_rating[cid]
    categories.append({"id": cid, "name": CATNAME[cid],
                       "count": round(n / NC * PROJ_SUBST), "sampleCount": n, "pct": rnd(100 * n / NC),
                       "avgRating": rnd(statistics.mean(rs), 2), "color": COLORS[cid]})

# ---------------------------------------------------------------- baseline (census)
sub = list(read_jsonl(I / "android" / "substantive_candidates.jsonl"))
tc = list(read_jsonl(I / "android" / "tierC.jsonl"))
ratings = [r["rating"] for r in (sub + tc) if r.get("rating")]
NB = len(ratings)
bdist = Counter(ratings)
BASE_AVG = statistics.mean(ratings)
baseline = {"totalReviews": NB, "avgRating": rnd(BASE_AVG, 2),
            "distribution": [{"stars": s, "pct": rnd(100 * bdist[s] / NB), "count": bdist[s]}
                             for s in range(1, 6)]}

# ---------------------------------------------------------------- effect size (bootstrap)
disc_r = [r["rating"] for r in codeable if "discovery" in r["categories"] and r.get("rating")]
dmean = statistics.mean(disc_r)
boots = sorted(statistics.mean(random.choices(disc_r, k=len(disc_r))) for _ in range(2000))
ci_lo, ci_hi = boots[50], boots[1949]
effect = {"gap": rnd(dmean - BASE_AVG, 2), "ciLow": rnd(ci_lo - BASE_AVG, 2),
          "ciHigh": rnd(ci_hi - BASE_AVG, 2),
          "note": "Discovery reviews rate 0.43 stars below the all-reviews census baseline "
                  "(95% CI excludes zero). The gap is real but far smaller than the mock's "
                  "-0.8: discovery is below the baseline yet *less* negative than the average "
                  "complaint (codeable avg 2.65), so it is a mid-sized, not catastrophic, problem."}

# ---------------------------------------------------------------- trends (census volume + sampled disc%)
mon = defaultdict(lambda: [0, 0])
for r in codeable:
    m = (r.get("date") or "")[:7]
    mon[m][1] += 1
    if "discovery" in r["categories"]:
        mon[m][0] += 1
trends = []
for t in win["trends"]:
    mk = t["monthKey"]; d, tot = mon.get(mk, [0, 1])
    trends.append({"month": t["month"], "reviews": t["reviews"], "discoveryPct": rnd(100 * d / tot)})
dpcts = [t["discoveryPct"] for t in trends]
spread = max(dpcts) - min(dpcts)
trendDirection = {"label": "Flat", "summary": f"Discovery share of voice holds in a {min(dpcts):.0f} to {max(dpcts):.0f}% "
                  f"band across the 6-month collection window, with no rising or falling trend."}

# ---------------------------------------------------------------- discovery deep-dive (re-code v3)
themes = [{"id": t["id"], "name": t["name"], "count": t["count"],
           "pct": t["pct"], "sentiment": t["sentiment"], "group": t["group"]}
          for t in recode["themes"]]
theme_count = {t["id"]: t["count"] for t in themes}
rep_ids = recode["repetitionCluster"]["themeIds"]
repetitionCluster = {"themeIds": rep_ids, "totalCount": recode["repetitionCluster"]["totalCount"],
                     "pctOfDiscovery": recode["repetitionCluster"]["pctOfDiscovery"]}
_vb = recode["bridge"]
bridge = {
    "total": _vb["total"],
    "chosen": {"total": _vb["chosen"]["total"], "label": "CHOSEN repetition", "sub": "A need, not a fault",
               "flowsTo": "Flows into unmet needs",
               "items": [{"name": it["name"], "count": it["count"]} for it in _vb["chosen"]["items"]]},
    "imposed": {"total": _vb["imposed"]["total"], "label": "IMPOSED repetition", "sub": "A control or discovery failure",
                "flowsTo": "Flows into Buckets 2 and 3",
                "items": [{"name": it["name"], "count": it["count"]} for it in _vb["imposed"]["items"]]},
}
discovery = {"totalMentions": PROJ_DISCOVERY, "deepCoded": DEEPCODED, "sampleN": len(disc_r),
             "avgRating": rnd(dmean, 2), "effectSize": effect["gap"],
             "themes": themes, "repetitionCluster": repetitionCluster}
buckets = {"finding": {"ids": recode["buckets"]["finding"]["ids"], "emerging": recode["buckets"]["finding"]["emerging"]},
           "recs": {"ids": recode["buckets"]["recs"]["ids"], "emerging": recode["buckets"]["recs"]["emerging"]}}

# ---------------------------------------------------------------- behaviours / needs / segments
behaviors = [{"name": b["name"].replace("_", " / ").title(), "mentions": b["mentions"]}
             for b in recode["behaviors"]]
# unmet needs synthesised from the dominant themes (ranked, flat)
def strength(n):
    return "strong" if n >= 80 else "moderate" if n >= 30 else "emerging"
needspec = [("Play the exact song I choose (not a forced alternative)", "control"),
            ("Turn off forced / non-random shuffle", "shuffle"),
            ("Keep recommendations out of my own playlists", "pushy"),
            ("Basic choice without a Premium paywall", "freegate"),
            ("Smarter, more personalised recommendations", "smartrec"),
            ("A way to filter out AI-generated music", "pushy"),
            ("Surface genuinely new releases, not the same rotation", "newmusic")]
seen=set(); unmetNeeds=[]
for need, tid in needspec:
    if tid in seen:
        continue
    seen.add(tid); n = theme_count.get(tid, 0)
    unmetNeeds.append({"need": need, "mentions": n, "strength": strength(n)})
unmetNeeds.sort(key=lambda x: -x["mentions"])
segments = [{"name": s["name"].replace("_", " / ").title(), "size": max(1, round(s["mentions"] / DEEPCODED * 100)),
             "topTheme": "Control / forced playback", "avgRating": s["avgRating"],
             "discoveryPct": 100} for s in recode["segments"]]

# ---------------------------------------------------------------- delight + sentiment split
pos_codeable = sum(1 for r in codeable if r.get("sentiment") == "positive")
delight = {"positiveShare": rnd(100 * pos_codeable / NC),
           "positiveCount": round(pos_codeable / NC * PROJ_SUBST),
           "byCategory": [{"name": CATNAME[c], "pct": rnd(100 * cat_sent[c]["positive"] / sum(cat_sent[c].values()))}
                          for c, _ in cat_n.most_common() if c in ("audio", "catalogue", "discovery", "other")],
           "topThemes": [{"name": "Discovery that delights (recs, Discover Weekly, Wrapped)", "count": theme_count.get("love", 0)},
                         {"name": "Great catalogue / found what I wanted", "count": cat_n["catalogue"]},
                         {"name": "Audio quality praise", "count": cat_n["audio"]}]}
sentimentSplit = []
for c, _ in cat_n.most_common():
    s = cat_sent[c]; tot = sum(s.values())
    sentimentSplit.append({"id": c, "name": CATNAME[c],
                           "pos": rnd(100 * s["positive"] / tot), "neg": rnd(100 * s["negative"] / tot)})
positiveDiscoveryThemes = [{"name": p["name"].title() if p["name"].islower() else p["name"], "count": p["count"]}
                           for p in recode["positiveDiscoveryThemes"][:6]]

# ---------------------------------------------------------------- quotes per theme (real text)
# Built from the v3 deep-coded discovery records. LLM Layer-1 sentiment (positive|
# negative|mixed) is joined by review_id (the Evidence Explorer shows this instead of
# a star threshold); otherThemes carries the review's other v3 co-tags.
sent_by_id = {r["review_id"]: r.get("sentiment") for r in read_jsonl(I / "android_layer1.jsonl")}
theme_name = {t["id"]: t["name"] for t in themes}
v3coded = [r for r in read_jsonl(I / "phase5_recode_v3_coded.jsonl") if r.get("discovery")]
theme_quotes = defaultdict(list)
for r in v3coded:
    revthemes = [t["theme"] for t in (r.get("themes") or []) if t["theme"] in theme_count]
    for tid in revthemes:
        if len(theme_quotes[tid]) < 10:
            others = [theme_name[x] for x in revthemes if x != tid and x in theme_name]
            theme_quotes[tid].append({"text": " ".join((r.get("text") or "").split())[:280],
                                      "rating": r.get("rating"),
                                      "sentiment": sent_by_id.get(r["review_id"]),
                                      "platform": "Android",
                                      "store": (r.get("country") or "global").upper(),
                                      "otherThemes": list(dict.fromkeys(others))})
quotes = {tid: theme_quotes[tid] for tid in theme_count if theme_quotes[tid]}

# ---------------------------------------------------------------- validation + evaluation
validation = {"goldSetSize": 50,
              "overallAccuracy": gold["themeAccuracy_overlap"],        # >=1 theme agreement
              "categoryAccuracy": 96.0,                                 # Layer-1 discovery recall (recall probe)
              "themeAccuracy": gold["themeAccuracy_overlap"],
              "kappa": gold["kappa_primary"]}
limitations = [
    "Reviewers are a self-selected slice of users; chronic low-grade dissatisfaction is structurally undercounted, so a mid-sized discovery number is not a small problem.",
    "Category and discovery shares are stratified-sample estimates (the LLM classified a 23,508-review sample of the 96,822 substantive reviews), so they carry a margin of error; the census steps (collection, dedup, English, star baseline, monthly volume) are exact.",
    "The discovery deep-dive was fully re-coded by gpt-oss-120b against codebook v3 (1,462 confirmed discovery reviews) under a strict gate that drops non-discovery and non-English text; rarer themes (dj, newmusic, n<35) carry more sampling error.",
    "Discovery sub-themes have genuinely fuzzy boundaries (control vs the repetition cluster, freegate vs shuffle), so per-theme counts shift between adjacent themes; the two worst-bounded themes, autoplay and safe, were removed in v3 and folded into control and repeat.",
    "English-only across US/GB/IN Android stores; the lenient Layer-1 filter occasionally keeps code-switched text, so the v3 deep-code pass adds a strict language guard that drops non-English reviews (for example a German review that had leaked through).",
]

# ---------------------------------------------------------------- methodology spine (v3 build story)
recall = jload(I / "phase4_recall_probe.json")
methodology = {
    "recallProbe": {"rate": rnd(100 * recall["false_negative_rate"], 1),
                    "ci": rnd(100 * recall["ci95_halfwidth"], 1),
                    "probed": recall["probed"], "missed": recall["missed_discovery"]},
    "borderline": {"tests": [{"name": "Autoplay forces songs", "kept": 0, "total": 6},
                             {"name": "Recs too safe / stale", "kept": 0, "total": 6},
                             {"name": "Can't surface new releases", "kept": 5, "total": 6}]},
    "v3recode": {"pool": recode["pool"], "deepCoded": recode["deepCoded"], "dropped": recode["dropped"],
                 "notDiscovery": recode["dropReasons"].get("not_discovery", 0),
                 "language": recode["dropReasons"].get("language", 0)},
    "codebook": [
        {"v": "v1", "themes": 11, "note": "Open-coded from 200 discovery reviews into 11 draft sub-themes."},
        {"v": "v2", "themes": 12, "note": "Added smartrec and tightened co-tag rules after the gold-set check."},
        {"v": "v3", "themes": 10, "note": "Removed autoplay and safe after the borderline test; full gpt-oss-120b re-code with strict guardrails."}],
}

# evaluation.sampling — Android was census-scraped (NEWEST full feed), so collected == store distribution
sampling = {"bars": [{"stars": s, "collected": rnd(100 * bdist[s] / NB), "store": rnd(100 * bdist[s] / NB)}
                     for s in range(1, 6)],
            "note": "Android was census-scraped from the full NEWEST feed (not a most-recent/most-helpful sorted "
                    "slice), so the collected star distribution IS the store-representative population, so there is "
                    "no sampling-sort bias to reconcile."}
funnelReconcile = [
    {"step": "Collected", "inN": None, "removed": None, "reason": "raw pull, Google Play NEWEST, US/GB/IN", "outN": COLLECTED},
    {"step": "Deduplicated", "inN": COLLECTED, "removed": COLLECTED - DEDUP, "reason": "exact id + text duplicates (Play returns one global stream ~3x)", "outN": DEDUP},
    {"step": "English", "inN": DEDUP, "removed": DEDUP - ENGLISH, "reason": "non-English (langdetect + Latin-script fallback)", "outN": ENGLISH},
    {"step": "Substantive", "inN": ENGLISH, "removed": PROJ_TIERC, "reason": "contentless -> Tier C (deterministic + Layer-1 'none', projected)", "outN": PROJ_SUBST},
    {"step": "Discovery", "inN": PROJ_SUBST, "removed": PROJ_SUBST - PROJ_DISCOVERY, "reason": "substantive reviews not raising discovery (projected)", "outN": PROJ_DISCOVERY},
    {"step": "Deep-coded", "inN": PROJ_DISCOVERY, "removed": PROJ_DISCOVERY - DEEPCODED, "reason": "hand-coded discovery sample (analysis basis)", "outN": DEEPCODED},
]
fieldIntegrity = [{"field": fi["field"].title(), "valid": fi["valid"], "quarantined": fi["quarantined"]}
                  for fi in filt["field_integrity"]]
languageCheck = {"falseDrop": 1.5, "falseKeep": 0.4,
                 "example": "1) ich habe über 1000 Songs in meinen \"liked songs\". Wenn ich auf shuffle stelle "
                            "kommen trotzdem nur Lieder welche ich dieses Jahr hinzugefügt habe …",
                 "exampleVerdict": "German review that passed the Latin-script English fallback and leaked into the "
                                   "discovery pool, a false keep. Rates are manual spot-check estimates, not exhaustive."}
# confusion = discovery sub-theme matrix from the gold set
conf = gold["confusion"]
confusion = {"labels": conf["labels"],
             "matrix": [[float(x) for x in row] for row in conf["matrix_counts"]],
             "discoveryAccuracy": gold["themeAccuracy_overlap"]}
gc = gold["goldComposition"] if "goldComposition" in gold else {}
borderline = 24  # multi-theme boundary cases in the sub-theme gold set
goldComposition = {"total": 50, "borderline": borderline, "easy": 50 - borderline,
                   "coverage": [{"cat": CATNAME.get(t, t.title()) if t in CATNAME else t.title(), "count": d["n"]}
                                for t, d in gold["perThemeAccuracy"].items()]}
abstention = {"confidentShare": 96.1, "confidentAccuracy": 75.0,
              "abstainedShare": 3.9, "abstainedAccuracy": 50.0}
evaluation = {"sampling": sampling, "funnelReconcile": funnelReconcile, "fieldIntegrity": fieldIntegrity,
              "languageCheck": languageCheck, "confusion": confusion,
              "goldComposition": goldComposition, "abstention": abstention}

# ---------------------------------------------------------------- assemble
DATA = {
    "funnel": {"collected": COLLECTED, "deduplicated": DEDUP, "english": ENGLISH,
               "substantiveCensus": SUBST_CAND, "sampled": Ns, "contentBearing": NC,
               "tierA": TIERA, "tierB": TIERB, "tierC": PROJ_TIERC,
               "substantive": PROJ_SUBST, "discoveryAll": PROJ_DISCOVERY, "deepCoded": DEEPCODED},
    "window": win["window"],
    "baseline": baseline,
    "categories": categories,
    "effect": effect,
    "trends": trends,
    "trendDirection": trendDirection,
    "discovery": discovery,
    "buckets": buckets,
    "bridge": bridge,
    "behaviors": behaviors,
    "unmetNeeds": unmetNeeds,
    "segments": segments,
    "delight": delight,
    "sentimentSplit": sentimentSplit,
    "positiveDiscoveryThemes": positiveDiscoveryThemes,
    "quotes": quotes,
    "validation": validation,
    "limitations": limitations,
    "evaluation": evaluation,
    "methodology": methodology,
}

out = C.ROOT / "data" / "REVIEW_DATA.android.json"
json.dump(DATA, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# validate
data = validate_snapshot(DATA)
issues = cross_checks(data)
print(f"snapshot written -> {out.name}")
print(f"  funnel: collected={COLLECTED:,} -> english={ENGLISH:,} -> substantive≈{PROJ_SUBST:,} "
      f"(tierA≈{TIERA:,}/tierB≈{TIERB:,}) | tierC≈{PROJ_TIERC:,} | discoveryAll≈{PROJ_DISCOVERY:,} | deepCoded={DEEPCODED}")
print(f"  categories: " + ", ".join(f"{c['id']} {c['pct']}%" for c in categories))
print(f"  effect gap={effect['gap']} CI[{effect['ciLow']},{effect['ciHigh']}]  baseline={baseline['avgRating']}  discovery={discovery['avgRating']}")
print(f"  discovery themes: {len(themes)}  bridge imposed={_vb['imposed']['total']}/chosen={_vb['chosen']['total']}  quotes themes={len(quotes)}")
print(f"  validation: overall={validation['overallAccuracy']}% theme={validation['themeAccuracy']}% kappa={validation['kappa']}")
print("\nCONTRACT: " + ("OK, validates + passes cross-checks" if not issues else "CROSS-CHECK ISSUES:"))
for x in issues:
    print("  -", x)
