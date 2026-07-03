"""Phase 5 — Claude re-code harness (codebook v2, FULL corpus, deadline pass).

Re-codes ALL 1,792 discovery reviews against codebook v2, by Claude's own judgment
(no open model — avoids rate limits). The full corpus is coded so the theme
WEIGHTINGS are correct, not just a sample. Canonical full re-code stays gpt-oss-120b
for later; this is the deadline pass.

Workflow (Claude drives it across batches):
  build               -> write all 1,792 items with stable gids
  dump START END      -> print a compact numbered list for Claude to read & code
  (Claude appends labels to phase5_recode_labels.jsonl, one obj/line)
  merge               -> aggregate the FULL corrected distribution + bridge + buckets
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict

from common import config as C
from common.io import read_jsonl, write_json

sys.stdout.reconfigure(encoding="utf-8")

NAMES = {"repeat": "Same songs on repeat", "shuffle": "Shuffle isn't random",
         "autoplay": "Autoplay forces songs", "safe": "Recs too safe / stale",
         "mismatch": "Irrelevant / wrong recs", "pushy": "Unwanted recs pushed",
         "smartrec": "Wants smarter / personalized recs", "control": "No control over recs",
         "freegate": "Free tier blocks discovery", "dj": "AI DJ problems",
         "newmusic": "Can't surface new releases", "love": "Discovery that delights",
         "emerging": "Other / emerging"}
GROUP = {"repeat": "repetition", "shuffle": "repetition", "autoplay": "repetition",
         "safe": "relevance", "mismatch": "relevance", "pushy": "relevance", "smartrec": "relevance",
         "control": "features", "freegate": "features", "dj": "features", "newmusic": "features",
         "love": "positive", "emerging": "features"}
BUCKET = {"control": "finding", "freegate": "finding", "dj": "finding", "newmusic": "finding",
          "safe": "recs", "mismatch": "recs", "pushy": "recs", "smartrec": "recs"}
REPETITION = {"repeat", "shuffle", "autoplay"}

ITEMS = C.INTERIM_DIR / "phase5_recode_items.jsonl"
LABELS = C.INTERIM_DIR / "phase5_recode_labels.jsonl"


def build():
    pool = [r for r in read_jsonl(C.INTERIM_DIR / "phase5_discovery_coded.jsonl")
            if r.get("discovery") and (r.get("text") or "").strip()]
    with open(ITEMS, "w", encoding="utf-8") as fh:
        for i, r in enumerate(pool, 1):
            fh.write(json.dumps({"gid": i, "review_id": r["review_id"], "rating": r.get("rating"),
                                 "country": r.get("country"), "date": r.get("date"),
                                 "text": r.get("text"), "v1_themes": [t["theme"] for t in (r.get("themes") or [])]},
                                ensure_ascii=False) + "\n")
    print(f"built {len(pool)} items -> {ITEMS.name}  (code in batches via `dump START END`)")


def dump(start, end):
    for r in read_jsonl(ITEMS):
        if start <= r["gid"] <= end:
            txt = " ".join((r["text"] or "").split())
            print(f'{r["gid"]}. [{r["rating"]}*] {txt}')


def merge():
    labels = {l["gid"]: l for l in read_jsonl(LABELS)}
    items = {r["gid"]: r for r in read_jsonl(ITEMS)}
    done = sorted(labels)
    missing = [g for g in items if g not in labels]
    coded = [labels[g] for g in done]
    disc = [l for l in coded if "not_discovery" not in (l.get("themes") or [])]
    notdisc = [l for l in coded if "not_discovery" in (l.get("themes") or [])]
    D = len(disc)

    theme_n = Counter(); theme_rating = defaultdict(list); rep = Counter()
    for l in disc:
        ths = [t for t in (l.get("themes") or []) if t in NAMES]
        for t in set(ths):
            theme_n[t] += 1
            theme_rating[t].append(items.get(l["gid"], {}).get("rating"))
        if any(t in REPETITION for t in ths) and l.get("repetition") in ("chosen", "imposed"):
            rep[l["repetition"]] += 1

    def avg(xs):
        xs = [x for x in xs if x]
        return round(sum(xs) / len(xs), 2) if xs else None

    themes = [{"id": t, "name": NAMES[t], "group": GROUP[t], "bucket": BUCKET.get(t),
               "count": c, "pct": round(100 * c / D, 1) if D else 0, "avgRating": avg(theme_rating[t])}
              for t, c in theme_n.most_common()]
    rep_total = sum(rep.values())
    out = {"labeled": len(coded), "remaining": len(missing), "discovery": D,
           "not_discovery": len(notdisc),
           "themes": themes,
           "repetitionCluster": {"total": sum(theme_n[t] for t in REPETITION),
                                 "chosen": rep["chosen"], "imposed": rep["imposed"]},
           "buckets": {"finding": [t["id"] for t in themes if t["bucket"] == "finding"],
                       "recs": [t["id"] for t in themes if t["bucket"] == "recs"]}}
    write_json(C.INTERIM_DIR / "phase5_recode_analysis.json", out)
    print(f"labeled {len(coded)}/{len(items)}  (remaining {len(missing)})  discovery={D} not_discovery={len(notdisc)}")
    if missing:
        print(f"  next ungraded gid: {missing[0]}")
    print(f"\n{'theme':11s} {'n':>4} {'pct':>6} {'rating':>6}  group/bucket")
    for t in themes:
        print(f"  {t['id']:9s} {t['count']:4d} {t['pct']:5.1f}% {str(t['avgRating']):>6}  {t['group']}/{t['bucket']}")
    print(f"\nrepetition: imposed={rep['imposed']} chosen={rep['chosen']} (of {rep_total} labeled)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    d = sub.add_parser("dump"); d.add_argument("start", type=int); d.add_argument("end", type=int)
    sub.add_parser("merge")
    a = ap.parse_args()
    {"build": lambda: build(), "merge": lambda: merge(),
     "dump": lambda: dump(a.start, a.end)}[a.cmd]()
