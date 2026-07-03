"""Phase 5 — borderline sub-theme tightening test.

Pulls a BLIND, randomized sample from the fuzzy/borderline discovery themes in the
690-review Claude re-code (codebook v2), so the user can re-label them independently
and we can measure where those themes are over/under-applied. The findings then drive
a codebook tweak before the remaining ~1,200 reviews are deep-coded on gpt-oss-120b.

Borderline themes under test: autoplay, safe, newmusic, and the other/emerging bucket
(emerging + not_discovery).

Build the sheet:   python -m phases.phase-5-layer2-discovery.borderline_test build
Score it back:     python -m phases.phase-5-layer2-discovery.borderline_test score

Inputs : data/interim/phase5_recode_labels.jsonl  (gid, themes, repetition)
         data/interim/phase5_recode_items.jsonl   (gid, text, rating, country, ...)
Outputs: data/interim/borderline_sheet.csv        (BLIND — user fills your_themes)
         data/interim/borderline_key.json         (HIDDEN — original Claude labels)
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict

from common import config as C

sys.stdout.reconfigure(encoding="utf-8")

I = C.INTERIM_DIR
LABELS = I / "phase5_recode_labels.jsonl"
ITEMS = I / "phase5_recode_items.jsonl"
SHEET = I / "borderline_sheet.csv"
KEY = I / "borderline_key.json"

SEED = 42
# how many to pull per borderline theme (other/emerging takes all available)
SAMPLE = {"autoplay": 6, "safe": 6, "newmusic": 6}
OTHER_BUCKET = ["emerging", "not_discovery"]   # combined into one "other" group

VALID_IDS = ["repeat", "shuffle", "autoplay", "safe", "mismatch", "pushy", "smartrec",
             "control", "freegate", "dj", "newmusic", "love", "emerging", "not_discovery"]


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def build():
    labels = read_jsonl(LABELS)
    items = {r["gid"]: r for r in read_jsonl(ITEMS)}
    rng = random.Random(SEED)

    # index gids by the borderline theme they carry
    by_theme = defaultdict(list)
    for r in labels:
        for t in (r.get("themes") or []):
            by_theme[t].append(r["gid"])

    picks = []  # (gid, sampled_from)
    for theme, n in SAMPLE.items():
        pool = sorted(set(by_theme.get(theme, [])))
        chosen = rng.sample(pool, min(n, len(pool)))
        picks += [(g, theme) for g in chosen]

    # other/emerging bucket: take ALL available (it's tiny)
    other_gids = sorted({g for t in OTHER_BUCKET for g in by_theme.get(t, [])})
    picks += [(g, "other") for g in other_gids]

    # dedup gids (a review can carry two borderline themes), keep first label-of-record
    seen = {}
    for g, src in picks:
        seen.setdefault(g, src)
    rows = [(g, src) for g, src in seen.items()]
    rng.shuffle(rows)

    label_by_gid = {r["gid"]: r for r in labels}
    key = {}
    with open(SHEET, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["row", "gid", "rating", "review_text",
                    "your_themes", "your_repetition_type", "notes"])
        for i, (gid, src) in enumerate(rows, 1):
            it = items.get(gid, {})
            text = " ".join((it.get("text") or "").split())
            w.writerow([i, gid, it.get("rating", ""), text, "", "", ""])
            orig = label_by_gid.get(gid, {})
            key[str(gid)] = {"row": i, "sampled_from": src,
                             "themes": orig.get("themes", []),
                             "repetition": orig.get("repetition", "")}

    json.dump({"seed": SEED, "n": len(rows), "key": key},
              open(KEY, "w", encoding="utf-8"), indent=2)

    src_counts = Counter(src for _, src in rows)
    print(f"BLIND sheet written -> {SHEET}  ({len(rows)} reviews)")
    print(f"HIDDEN key  written -> {KEY.name}  (do not open before labeling)")
    print("  composition (by sampled-from theme): " +
          ", ".join(f"{k}={v}" for k, v in src_counts.items()))
    print("  fill `your_themes` (comma-separated ids) + `your_repetition_type` "
          "(chosen/imposed, only for repeat/shuffle/autoplay), then run `score`.")
    print("  valid ids: " + ", ".join(VALID_IDS))


def _parse_ids(s):
    return [x.strip().lower() for x in (s or "").replace(";", ",").split(",") if x.strip()]


def score():
    key = json.load(open(KEY, encoding="utf-8"))["key"]
    rows = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    filled = [r for r in rows if (r.get("your_themes") or "").strip()]
    if not filled:
        print("No labels found in `your_themes` yet — fill the sheet first, then re-run `score`.")
        return

    overlap_hits = exact_hits = 0
    confirm = defaultdict(lambda: [0, 0])   # theme -> [confirmed, total] for sampled-from theme
    reassign = defaultdict(Counter)         # borderline theme -> where the user moved it
    detail = []
    for r in filled:
        gid = r["gid"]
        k = key.get(str(gid), {})
        orig = set(k.get("themes", []))
        mine = set(_parse_ids(r.get("your_themes")))
        src = k.get("sampled_from", "?")
        ov = bool(orig & mine)
        ex = orig == mine
        overlap_hits += ov
        exact_hits += ex
        # did the user keep the borderline theme this row was sampled for?
        probe = src if src != "other" else None
        if probe:
            confirm[probe][1] += 1
            if probe in mine:
                confirm[probe][0] += 1
            else:
                for m in mine:
                    reassign[probe][m] += 1
        detail.append((int(r["row"]), gid, src, sorted(orig), sorted(mine), ov, ex))

    n = len(filled)
    print(f"=== Borderline test scored ({n} labeled rows) ===\n")
    print(f"  >=1 theme overlap with original : {overlap_hits}/{n}  ({100*overlap_hits/n:.0f}%)")
    print(f"  exact theme-set match           : {exact_hits}/{n}  ({100*exact_hits/n:.0f}%)\n")
    print("  Per borderline theme — did YOU keep the label Claude assigned?")
    for t, (c, tot) in confirm.items():
        moved = ", ".join(f"{k}:{v}" for k, v in reassign[t].most_common(3))
        print(f"    {t:10} confirmed {c}/{tot}" + (f"   (when dropped, you used: {moved})" if moved else ""))
    print("\n  Row-by-row (row gid sampled_from | original -> yours | overlap exact):")
    for row, gid, src, orig, mine, ov, ex in sorted(detail):
        flag = "OK " if ex else ("~  " if ov else "XX ")
        print(f"    {flag}r{row:<3} {gid:<5} {src:9} | {orig} -> {mine}")
    print("\n  XX = no overlap (likely a real mislabel)   ~ = partial   OK = exact")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd == "score":
        score()
    else:
        print("usage: borderline_test.py [build|score]")
