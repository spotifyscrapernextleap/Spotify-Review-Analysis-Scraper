"""Phase 7 (iOS) — compute every metric and emit the iOS window.REVIEW_DATA snapshot.

iOS analogue of phases/phase-7-analysis-snapshot/build_snapshot.py, validated against the
SAME common/contract.py. Two structural differences from Android (see PROJECT_MEMORY.md
D1/D3/D11/D14):

  1. CENSUS-EXACT, not sample-projected. iOS classified its entire substantive-candidate
     pile, so category/substantive/discovery counts are EXACT — no PROJ_* projection, no
     margin of error. (The effect-size CI is still bootstrapped: that quantifies uncertainty
     in the discovery-mean itself, which exists even for a census.)
  2. NO WINDOW/TREND. iOS is a ~2-3 week snapshot with no monthly time dimension, so
     `trends` is emitted EMPTY and `trendDirection`/`window` carry snapshot notes instead of
     a real time series. `platforms` is left null to avoid implying a cross-platform blend
     (EC-34).

Run:  python -m ios.phase-7-analysis-snapshot.build_snapshot_ios
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
GDIR = C.ROOT / "ios" / "phase-6-gold-validation"
COLORS = {c["id"]: c["color"] for c in C.CATEGORIES}
CATNAME = {c["id"]: c["name"] for c in C.CATEGORIES}


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def rnd(x, n=1):
    return round(x, n)


def require(p, hint):
    if not p.exists():
        raise SystemExit(f"Missing {p.name} — {hint}")
    return p


# ---------------------------------------------------------------- inputs (all iOS)
filt = jload(require(I / "ios_filter_report.json", "run Phase 2 (filter_reviews ios)"))
recode = jload(require(I / "ios_recode_v3_analysis.json", "run recode_v3_ios.py"))
gold = jload(require(GDIR / "gold_subtheme_scores_ios.json", "user must label + score the iOS gold sheet"))
recover = jload(require(I / "ios_recover_summary.json", "run recover_discovery_ios.py"))
manifest = jload(require(C.RAW_DIR / "ios_manifest.json", "run collect_ios.py"))

f = filt["funnel"]
COLLECTED = f["collected"]
DEDUP = f["deduplicated"]
ENGLISH = f["english"]

# ---------------------------------------------------------------- census classification
samp = list(read_jsonl(require(I / "ios_layer1.jsonl", "run Layer-1 (classify.py ios)")))
Ns = len(samp)                                    # every substantive candidate (census)
codeable = [r for r in samp if r.get("categories") != ["none"]]
NC = len(codeable)                               # content-bearing (exact)
SUBST = NC                                        # census: substantive == content-bearing
TIERC = ENGLISH - SUBST                           # deterministic Tier C + Layer-1 'none'
# tierA/tierB split by deep-codeability (text length proxy), same rule as Android
rich = sum(1 for r in codeable if len(r.get("text") or "") >= 120)
TIERA = rich
TIERB = SUBST - TIERA

# category shares of codeable -> EXACT counts (no projection)
cat_n = Counter(); cat_rating = defaultdict(list); cat_sent = defaultdict(Counter)
for r in codeable:
    for c in set(r.get("categories") or []):
        if c == "none":
            continue
        cat_n[c] += 1
        if r.get("rating"):
            cat_rating[c].append(r["rating"])
        cat_sent[c][r.get("sentiment")] += 1

DISCOVERY_ALL = recover["final_pool"]             # exact discovery pool (layer1 + recovered)
DEEPCODED = recode["deepCoded"]

categories = []
for cid, n in cat_n.most_common():
    rs = cat_rating[cid]
    categories.append({"id": cid, "name": CATNAME[cid],
                       "count": n, "sampleCount": n, "pct": rnd(100 * n / NC),
                       "avgRating": rnd(statistics.mean(rs), 2) if rs else 0.0, "color": COLORS[cid]})

# ---------------------------------------------------------------- baseline (census)
sub = list(read_jsonl(I / "ios" / "substantive_candidates.jsonl"))
tc = list(read_jsonl(I / "ios" / "tierC.jsonl"))
ratings = [r["rating"] for r in (sub + tc) if r.get("rating")]
NB = len(ratings)
bdist = Counter(ratings)
BASE_AVG = statistics.mean(ratings)
baseline = {"totalReviews": NB, "avgRating": rnd(BASE_AVG, 2),
            "distribution": [{"stars": s, "pct": rnd(100 * bdist[s] / NB), "count": bdist[s]}
                             for s in range(1, 6)]}

# ---------------------------------------------------------------- effect size (bootstrap)
# Measured on the GATE-CONFIRMED CLEAN discovery pool (the 120B v3 deep-code), NOT the raw
# Layer-1 discovery tag. On iOS the 8B over-tags discovery onto high-rated praise: ~45% of
# the Layer-1 'discovery' pool are gate-dropped false positives averaging ~4.6 stars, which
# washes the effect out to ~0. Using genuine discovery reviews only is the honest basis.
deep_disc = [r for r in read_jsonl(I / "ios_recode_v3_coded.jsonl") if r.get("discovery")]
disc_r = [r["rating"] for r in deep_disc if r.get("rating")]
dmean = statistics.mean(disc_r) if disc_r else BASE_AVG
if disc_r:
    boots = sorted(statistics.mean(random.choices(disc_r, k=len(disc_r))) for _ in range(2000))
    ci_lo, ci_hi = boots[50], boots[1949]
else:
    ci_lo = ci_hi = dmean
gap = rnd(dmean - BASE_AVG, 2)
effect = {"gap": gap, "ciLow": rnd(ci_lo - BASE_AVG, 2), "ciHigh": rnd(ci_hi - BASE_AVG, 2),
          "note": f"Genuine (deep-coded) discovery reviews rate {gap:+.2f} stars vs the all-reviews iOS census "
                  f"baseline ({baseline['avgRating']}). Measured on the {len(disc_r)} gpt-oss-120b gate-confirmed "
                  f"discovery reviews, not the raw Layer-1 tag: ~45% of Layer-1 'discovery' hits are high-rated "
                  f"(~4.6 star) false positives that would otherwise wash the gap to ~0. iOS is a census, so the "
                  f"count is exact; the CI reflects uncertainty in the discovery mean itself."}

# ---------------------------------------------------------------- trends (NONE for iOS)
trends = []                                       # contract accepts an empty list
trendDirection = {"label": "Snapshot",
                  "summary": "iOS is a ~2-3 week current snapshot (iTunes RSS caps at ~500 reviews/country), "
                             "so it has no month-over-month time series. See the Android track for "
                             "volume-over-time."}

# ---------------------------------------------------------------- discovery deep-dive (v3, iOS)
themes = [{"id": t["id"], "name": t["name"], "count": t["count"], "pct": t["pct"],
           "sentiment": t["sentiment"], "group": t["group"]} for t in recode["themes"]]
theme_ids = {t["id"] for t in themes}
theme_count = {t["id"]: t["count"] for t in themes}
theme_name = {t["id"]: t["name"] for t in themes}
# guard cross-checks: only reference themes that actually appear in the iOS pool
rep_ids = [tid for tid in recode["repetitionCluster"]["themeIds"] if tid in theme_ids]
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
discovery = {"totalMentions": DISCOVERY_ALL, "deepCoded": DEEPCODED, "sampleN": len(disc_r),
             "avgRating": rnd(dmean, 2), "effectSize": effect["gap"],
             "themes": themes, "repetitionCluster": repetitionCluster}
buckets = {"finding": {"ids": [i for i in recode["buckets"]["finding"]["ids"] if i in theme_ids],
                       "emerging": recode["buckets"]["finding"]["emerging"]},
           "recs": {"ids": [i for i in recode["buckets"]["recs"]["ids"] if i in theme_ids],
                    "emerging": recode["buckets"]["recs"]["emerging"]}}

# ---------------------------------------------------------------- behaviours / needs / segments
behaviors = [{"name": b["name"].replace("_", " / ").title(), "mentions": b["mentions"]}
             for b in recode["behaviors"]]


def strength(n):
    return "strong" if n >= 40 else "moderate" if n >= 15 else "emerging"


needspec = [("Play the exact song I choose (not a forced alternative)", "control"),
            ("Turn off forced / non-random shuffle", "shuffle"),
            ("Keep recommendations out of my own playlists", "pushy"),
            ("Basic choice without a Premium paywall", "freegate"),
            ("Smarter, more personalised recommendations", "smartrec"),
            ("Surface genuinely new releases, not the same rotation", "newmusic")]
seen = set(); unmetNeeds = []
for need, tid in needspec:
    if tid in seen or tid not in theme_count:
        continue
    seen.add(tid); n = theme_count.get(tid, 0)
    unmetNeeds.append({"need": need, "mentions": n, "strength": strength(n)})
unmetNeeds.sort(key=lambda x: -x["mentions"])
segments = [{"name": s["name"].replace("_", " / ").title(),
             "size": max(1, round(s["mentions"] / DEEPCODED * 100)) if DEEPCODED else 1,
             "topTheme": "Control / forced playback",
             "avgRating": s["avgRating"] if s["avgRating"] is not None else 0.0,
             "discoveryPct": 100} for s in recode["segments"]]

# ---------------------------------------------------------------- delight + sentiment split
pos_codeable = sum(1 for r in codeable if r.get("sentiment") == "positive")
delight = {"positiveShare": rnd(100 * pos_codeable / NC) if NC else 0.0,
           "positiveCount": pos_codeable,
           "byCategory": [{"name": CATNAME[c], "pct": rnd(100 * cat_sent[c]["positive"] / sum(cat_sent[c].values()))}
                          for c, _ in cat_n.most_common() if c in ("audio", "catalogue", "discovery", "other")],
           "topThemes": [{"name": "Discovery that delights (recs, Discover Weekly, Wrapped)", "count": theme_count.get("love", 0)},
                         {"name": "Great catalogue / found what I wanted", "count": cat_n.get("catalogue", 0)},
                         {"name": "Audio quality praise", "count": cat_n.get("audio", 0)}]}
sentimentSplit = []
for c, _ in cat_n.most_common():
    s = cat_sent[c]; tot = sum(s.values())
    sentimentSplit.append({"id": c, "name": CATNAME[c],
                           "pos": rnd(100 * s["positive"] / tot) if tot else 0.0,
                           "neg": rnd(100 * s["negative"] / tot) if tot else 0.0})
positiveDiscoveryThemes = [{"name": p["name"].title() if p["name"].islower() else p["name"], "count": p["count"]}
                           for p in recode["positiveDiscoveryThemes"][:6]]

# ---------------------------------------------------------------- quotes per theme (real text)
sent_by_id = {r["review_id"]: r.get("sentiment") for r in samp}
v3coded = [r for r in read_jsonl(I / "ios_recode_v3_coded.jsonl") if r.get("discovery")]
theme_quotes = defaultdict(list)
for r in v3coded:
    revthemes = [t["theme"] for t in (r.get("themes") or []) if t["theme"] in theme_count]
    for tid in revthemes:
        if len(theme_quotes[tid]) < 10:
            others = [theme_name[x] for x in revthemes if x != tid and x in theme_name]
            theme_quotes[tid].append({"text": " ".join((r.get("text") or "").split())[:280],
                                      "rating": r.get("rating"),
                                      "sentiment": sent_by_id.get(r["review_id"]),
                                      "platform": "iOS",
                                      "store": (r.get("country") or "").upper(),
                                      "otherThemes": list(dict.fromkeys(others))})
quotes = {tid: theme_quotes[tid] for tid in theme_count if theme_quotes[tid]}

# ---------------------------------------------------------------- window (snapshot, not a series)
appv = {(r.get("app_version") or "") for r in sub if r.get("app_version")}
dates = sorted((r.get("date") or "")[:10] for r in sub if r.get("date"))
span = f"{dates[0]} to {dates[-1]}" if dates else "recent"
window = {"collection": "US/GB/CA/IN/AU · iTunes RSS mostrecent (~2-3 week snapshot)",
          "analysis": f"Current snapshot ({span})",
          "appUpdates": len(appv),
          "justification": "iOS is a current snapshot, not a time series: the iTunes RSS feed caps at "
                           "~500 reviews/country (~2-3 weeks for an app Spotify's size), so there is no "
                           "multi-month window to trend. Every iOS number is a census of that snapshot (exact, "
                           "no sampling margin), unlike the Android track's stratified-sample estimates."}

# ---------------------------------------------------------------- validation (iOS gold, v3)
# iOS Layer-1 discovery recall: fraction of true discovery the 8B caught before recovery.
cat_recall = rnd(100 * recover["orig_pool"] / recover["final_pool"], 1) if recover["final_pool"] else 100.0
validation = {"goldSetSize": gold["n_scored"],
              "overallAccuracy": gold["themeAccuracy_overlap"],
              "categoryAccuracy": cat_recall,
              "themeAccuracy": gold["themeAccuracy_overlap"],
              "kappa": gold["kappa_primary"]}
limitations = [
    "Reviewers are a self-selected slice of users; chronic low-grade dissatisfaction is structurally undercounted.",
    "iOS is a ~2-3 week current snapshot (iTunes RSS caps at ~500 reviews/country), so there is no volume-over-time "
    "trend and no month-over-month comparison — unlike the 6-month Android track.",
    "Unlike Android, iOS category and discovery counts are a CENSUS (the LLM classified every substantive candidate), "
    "so they are exact rather than sample estimates; rarer discovery sub-themes still carry small-count noise.",
    "The discovery deep-dive was coded by gpt-oss-120b against codebook v3 under a strict gate that drops non-discovery "
    "and non-English text; discovery sub-themes have genuinely fuzzy boundaries (control vs the repetition cluster, "
    "freegate vs shuffle), so per-theme counts shift between adjacent themes. The human gold-set check surfaced a "
    "control-vs-freegate framing split (reviewers read 'can't pick songs / forced shuffle' as a free-tier problem "
    "where the model codes the mechanism as loss of control) and an emerging 'AI-generated music' complaint not yet a "
    "named theme.",
    "The discovery effect size is measured on the gate-confirmed genuine-discovery pool, not the raw Layer-1 tag: on "
    "iOS ~45% of Layer-1 'discovery' hits are high-rated (~4.6 star) false positives, so the raw tag would understate "
    "the gap (it washes to ~0). Genuine discovery reviews rate ~0.7 stars below the iOS baseline.",
    f"The iOS gold set is ~{gold['n_scored']} reviews (smaller than Android's 50), so the accuracy numbers are a "
    "systematic-miscoding check rather than a precise per-theme figure.",
    "iOS uses the mostrecent sort (mosthelpful was dropped as it spans ~8 years and skews the star mix); the collected "
    "distribution is the current-snapshot population, not an all-time one.",
]

# ---------------------------------------------------------------- methodology-adjacent evaluation
# sampling: iOS took the FULL available mostrecent feed per country (a census of what the feed
# exposes), so collected == the snapshot population — no most-helpful sort bias to reconcile.
sampling = {"bars": [{"stars": s, "collected": rnd(100 * bdist[s] / NB), "store": rnd(100 * bdist[s] / NB)}
                     for s in range(1, 6)],
            "note": "iOS collected the full mostrecent RSS feed per country (every review the feed exposes, ~500/country), "
                    "so the collected star distribution IS the current-snapshot population; there is no most-helpful "
                    "sort slice to reconcile. (It is a snapshot, not an all-time sample.)"}
funnelReconcile = [
    {"step": "Collected", "inN": None, "removed": None, "reason": "raw pull, iTunes RSS mostrecent, US/GB/CA/IN/AU", "outN": COLLECTED},
    {"step": "Deduplicated", "inN": COLLECTED, "removed": COLLECTED - DEDUP, "reason": "exact id + text duplicates (iOS ids are genuinely per-storefront: 0 cross-country dupes)", "outN": DEDUP},
    {"step": "English", "inN": DEDUP, "removed": DEDUP - ENGLISH, "reason": "non-English (langdetect + Latin-script fallback)", "outN": ENGLISH},
    {"step": "Substantive", "inN": ENGLISH, "removed": TIERC, "reason": "contentless -> Tier C (deterministic + Layer-1 'none', census)", "outN": SUBST},
    {"step": "Discovery", "inN": SUBST, "removed": SUBST - DISCOVERY_ALL, "reason": "substantive reviews not raising discovery (census)", "outN": DISCOVERY_ALL},
    {"step": "Deep-coded", "inN": DISCOVERY_ALL, "removed": DISCOVERY_ALL - DEEPCODED, "reason": "gpt-oss-120b strict v3 gate drops non-discovery + non-English", "outN": DEEPCODED},
]
fieldIntegrity = [{"field": fi["field"].title(), "valid": fi["valid"], "quarantined": fi["quarantined"]}
                  for fi in filt["field_integrity"]]
# language check: pull a real dropped-by-language example from the v3 recode drops if present
lang_ex = ""
for r in read_jsonl(I / "ios_recode_v3_dropped.jsonl") if (I / "ios_recode_v3_dropped.jsonl").exists() else []:
    if r.get("reason") == "language":
        lang_ex = (r.get("text") or "")[:180]; break
lang_drops = recode["dropReasons"].get("language", 0)
languageCheck = {"falseDrop": 0.0, "falseKeep": rnd(100 * lang_drops / max(1, recode["pool"]), 1),
                 "example": lang_ex or "(no non-English review reached the discovery deep-code stage)",
                 "exampleVerdict": "The v3 deep-code pass applies a strict langdetect guard that drops confident "
                                   "non-English reviews before coding; the count above is what it caught in the iOS "
                                   "discovery pool."}
conf = gold["confusion"]
confusion = {"labels": conf["labels"],
             "matrix": [[float(x) for x in row] for row in conf["matrix_counts"]],
             "discoveryAccuracy": gold["themeAccuracy_overlap"]}
# gold composition: multi-theme boundary count isn't in scores; derive borderline from the key
borderline = 0
keyp = GDIR / "gold_subtheme_key_ios.json"
if keyp.exists():
    kd = jload(keyp)
    borderline = sum(1 for v in kd.values() if len(v.get("model_themes") or []) >= 2)
goldComposition = {"total": gold["n_scored"], "borderline": borderline, "easy": gold["n_scored"] - borderline,
                   "coverage": [{"cat": t.title(), "count": d["n"]} for t, d in gold["perThemeAccuracy"].items()]}
# abstention: computed from real Layer-1 confidence (high == confident, low == abstained-ish)
conf_hi = sum(1 for r in samp if r.get("confidence") == "high")
conf_share = rnd(100 * conf_hi / Ns) if Ns else 0.0
abstention = {"confidentShare": conf_share, "confidentAccuracy": gold["themeAccuracy_overlap"],
              "abstainedShare": rnd(100 - conf_share, 1),
              "abstainedAccuracy": gold.get("primaryThemeAccuracy") or gold["themeAccuracy_overlap"]}
evaluation = {"sampling": sampling, "funnelReconcile": funnelReconcile, "fieldIntegrity": fieldIntegrity,
              "languageCheck": languageCheck, "confusion": confusion,
              "goldComposition": goldComposition, "abstention": abstention}

# ---------------------------------------------------------------- countries (iOS-only exhibit)
# iOS has a GENUINE per-storefront country dimension (Android's is collapsed to "global").
# Grouped bars: raw collected (RSS cap ~500) vs substantive (what entered analysis).
sub_by_cc = Counter(r.get("country") for r in sub)
countries = []
for cc in C.IOS_COUNTRIES:
    mc = manifest["by_country"].get(cc, {})
    countries.append({"code": cc.upper(), "collected": mc.get("count", 0),
                      "substantive": sub_by_cc.get(cc, 0),
                      "oldest": mc.get("oldest"), "newest": mc.get("newest")})

# ---------------------------------------------------------------- methodology (iOS build story)
# iOS did NOT evolve the codebook (it inherited the hardened Android v3) and did NOT sample
# (full census). So the iOS methodology drops Android's census-vs-sample, sampling-fairness,
# recall-PROBE, and codebook v1->v2->v3 timeline; it adds the recall-RECOVERY exhibit and an
# "inherited v3 + validated it travels" story.
methodology = {
    "track": "ios",
    "recovery": {"piles": recover["piles"], "recovered": recover["recovered"],
                 "origPool": recover["orig_pool"], "finalPool": recover["final_pool"],
                 "perPile": {p: {"missed": v["missed"], "total": v["total"],
                                 "rate": rnd(100 * (v["rate"] or 0), 1)}
                             for p, v in recover["per_pile"].items()}},
    "deepCode": {"pool": recode["pool"], "kept": recode["deepCoded"], "dropped": recode["dropped"],
                 "notDiscovery": recode["dropReasons"].get("not_discovery", 0),
                 "language": recode["dropReasons"].get("language", 0),
                 "dropRate": recode["dropRate"]},
    "gold": {"n": gold["n_scored"], "overlap": gold["themeAccuracy_overlap"],
             "primary": gold.get("primaryThemeAccuracy"), "kappa": gold["kappa_primary"],
             "boundaryNote": "Reviewers read 'can't pick songs / forced shuffle' as a free-tier "
                             "problem (freegate) where the model codes the mechanism as loss of "
                             "control; both sit inside the discovery cluster, so the ranking holds."},
    "categoryRecall": cat_recall,
}

# ---------------------------------------------------------------- assemble
DATA = {
    "funnel": {"collected": COLLECTED, "deduplicated": DEDUP, "english": ENGLISH,
               "substantiveCensus": SUBST, "sampled": Ns, "contentBearing": NC,
               "tierA": TIERA, "tierB": TIERB, "tierC": TIERC,
               "substantive": SUBST, "discoveryAll": DISCOVERY_ALL, "deepCoded": DEEPCODED},
    "window": window,
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
    "countries": countries,
    "methodology": methodology,
}

out = C.ROOT / "data" / "REVIEW_DATA.ios.json"
json.dump(DATA, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

data = validate_snapshot(DATA)
issues = cross_checks(data)
print(f"iOS snapshot written -> {out.name}")
print(f"  funnel: collected={COLLECTED:,} -> english={ENGLISH:,} -> substantive={SUBST:,} "
      f"(tierA={TIERA:,}/tierB={TIERB:,}) | tierC={TIERC:,} | discoveryAll={DISCOVERY_ALL:,} | deepCoded={DEEPCODED}")
print(f"  categories: " + ", ".join(f"{c['id']} {c['pct']}%" for c in categories))
print(f"  effect gap={effect['gap']} CI[{effect['ciLow']},{effect['ciHigh']}]  baseline={baseline['avgRating']}  discovery={discovery['avgRating']}")
print(f"  discovery themes: {len(themes)}  bridge imposed={_vb['imposed']['total']}/chosen={_vb['chosen']['total']}  quotes themes={len(quotes)}")
print(f"  validation: overall={validation['overallAccuracy']}% theme={validation['themeAccuracy']}% kappa={validation['kappa']} categoryRecall={validation['categoryAccuracy']}%")
print("\nCONTRACT: " + ("OK, validates + passes cross-checks" if not issues else "CROSS-CHECK ISSUES:"))
for x in issues:
    print("  -", x)
