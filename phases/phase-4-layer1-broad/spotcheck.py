"""Reusable Layer-1 agreement test (the user's blind spot-check, formalised).

Ground truth = 56 reviews the user blind-labelled across two rounds, with their
adjudication of the ambiguous cases (multi-label where they gave 2-3). `playback`
was renamed to `tech`.

Subcommands:
  build              -> data/interim/spotcheck_groundtruth.json  (from the round keys)
  validate           -> classify the 56 with the CURRENT prompt and score
  score <file.jsonl> -> score an existing model output (review_id + categories)

Match metric (multi-label): a review AGREES if model categories overlap the
ground-truth set (>=1 shared). Exact-set match reported separately.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from common import config as C  # noqa: E402
from common.io import read_jsonl, write_json  # noqa: E402

GT_PATH = C.INTERIM_DIR / "spotcheck_groundtruth.json"

# user labels (playback->tech, ambiguous rulings applied)
R1 = {1:["pricing"],2:["tech"],3:["discovery"],4:["audio"],5:["pricing"],6:["pricing","ux"],
      7:["pricing"],8:["ux","pricing"],9:["catalogue"],10:["audio"],11:["ux"],12:["tech"],
      13:["ux","discovery"],14:["ux"],15:["audio"],16:["ux"],17:["none"],18:["pricing"],
      19:["ux"],20:["none"],21:["discovery","ux"],22:["audio"],23:["none"],24:["catalogue"]}
R2 = {1:["audio","tech"],2:["tech"],3:["ux","discovery"],4:["none"],5:["ux"],6:["pricing"],
      7:["other"],8:["pricing"],9:["none"],10:["catalogue","discovery"],11:["none"],12:["tech"],
      13:["catalogue"],14:["ux","discovery"],15:["none"],16:["tech"],17:["pricing"],18:["audio"],
      19:["audio","catalogue"],20:["pricing"],21:["catalogue","ux"],22:["none"],23:["pricing"],
      24:["discovery"],25:["audio"],26:["discovery"],27:["pricing"],28:["tech"],
      29:["ux","audio","discovery"],30:["ux"],31:["pricing"],32:["pricing"]}


def _load_classify():
    spec = importlib.util.spec_from_file_location("classify", Path(__file__).resolve().parent / "classify.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def build():
    k1 = json.load(open(C.INTERIM_DIR / "phase4_spotcheck_key.json", encoding="utf-8"))
    k2 = json.load(open(C.INTERIM_DIR / "phase4_spotcheck_key2.json", encoding="utf-8"))
    texts = {r["review_id"]: r for r in read_jsonl(C.INTERIM_DIR / "android_layer1_sample.jsonl")}
    gt = {}
    for keymap, truth, rnd in ((k1, R1, 1), (k2, R2, 2)):
        for num, info in keymap.items():
            rid = info["review_id"]
            gt[rid] = {"labels": truth[int(num)], "round": rnd, "num": int(num),
                       "text": (texts.get(rid, {}).get("text") or "")[:200]}
    write_json(GT_PATH, gt)
    print(f"ground truth built: {len(gt)} reviews -> {GT_PATH}")


def score(model_path):
    gt = json.load(open(GT_PATH, encoding="utf-8"))
    model = {r["review_id"]: r.get("categories") or [r.get("category")]
             for r in read_jsonl(model_path)}
    overlap = exact = scored = 0
    misses = []
    cat_recall = {}  # cat -> [hit, total]
    for rid, g in gt.items():
        if rid not in model:
            continue
        scored += 1
        truth = set(g["labels"]); pred = set(model[rid])
        if truth & pred: overlap += 1
        else: misses.append((g["round"], g["num"], sorted(truth), sorted(pred), g["text"][:55]))
        if truth == pred: exact += 1
        for c in truth:
            cat_recall.setdefault(c, [0, 0]); cat_recall[c][1] += 1
            if c in pred: cat_recall[c][0] += 1
    print(f"SCORED {scored}/{len(gt)} | OVERLAP agreement {overlap}/{scored} = {100*overlap/scored:.0f}%"
          f" | exact-set {exact}/{scored} = {100*exact/scored:.0f}%")
    print("per-category recall (truth label caught by model):")
    for c in sorted(cat_recall):
        h, t = cat_recall[c]; print(f"   {c:10s} {h}/{t}")
    print(f"\nMISSES (no overlap) — {len(misses)}:")
    for rnd, num, t, p, txt in sorted(misses):
        print(f"   R{rnd}#{num}: truth={t} model={p} :: \"{txt}\"")


def validate():
    cl = _load_classify()
    gt = json.load(open(GT_PATH, encoding="utf-8"))
    sample = {r["review_id"]: r for r in read_jsonl(C.INTERIM_DIR / "android_layer1_sample.jsonl")}
    recs = [sample[rid] for rid in gt if rid in sample]
    recs, n_pod = cl.filter_podcast(recs)
    if n_pod:
        print(f"(filtered {n_pod} podcast-only from test set)")
    pool = cl.KeyPool(C.groq_api_keys())
    out_path = C.INTERIM_DIR / "spotcheck_modelrun.jsonl"
    with open(out_path, "w", encoding="utf-8") as fh:
        for rec, cats, sent, conf, _, _, _ in cl.classify_records(pool, recs, 20):
            fh.write(json.dumps({"review_id": rec["review_id"], "categories": cats,
                                 "sentiment": sent, "confidence": conf}, ensure_ascii=False) + "\n")
    print(f"classified {len(recs)} test reviews with prompt={cl.PROMPT_VERSION}; per-key tokens={pool.tokens}\n")
    score(out_path)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "build":
        build()
    elif cmd == "score":
        score(sys.argv[2])
    else:
        validate()
