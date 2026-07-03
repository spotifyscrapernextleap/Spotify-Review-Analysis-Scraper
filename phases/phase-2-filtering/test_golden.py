"""Phase 2 golden-set test (EC-6/7/8/10).

Asserts the deterministic filter behaves on the worked examples:
 - every tierA/tierB example survives as a substantive candidate (no false
   drops of real signal — esp. short-but-substantive g11/g24/g25),
 - non-English is flagged,
 - deterministically-catchable junk (emoji/char-repeat/spam/single word) -> tierC,
 - contentless-but-not-deterministic (long-but-empty, "best app ever") is allowed
   through as a candidate — it becomes Tier C after Layer-1 (rides on categorisation),
 - the near-duplicate pair g26/g27 collapses to one.
"""
import importlib.util
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.io import read_jsonl  # noqa: E402
from common import config as C  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "filter_mod", Path(__file__).resolve().parent / "filter_reviews.py")
filter_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(filter_mod)

GOLD = C.PHASES_DIR / "phase-0-foundations" / "golden_set.jsonl"

# Tier C cases that deterministic rules CANNOT catch (rely on Layer-1 -> Tier C).
# g13 = long-but-empty: real words, no codeable claim — only Layer-1 can route it.
RIDES_ON_LAYER1 = {"g13"}


def main() -> int:
    rows = list(read_jsonl(GOLD))
    by_id = {r["id"]: r for r in rows}
    fails = []

    for r in rows:
        if r["disposition"] == "drop_dupe":
            continue  # handled separately below
        got = filter_mod.classify_text(r["text"])
        disp = r["disposition"]
        if disp in ("tierA", "tierB"):
            expect = "substantive_candidate"
        elif disp == "drop_nonenglish":
            expect = "nonenglish"
        elif disp == "tierC":
            expect = "substantive_candidate" if r["id"] in RIDES_ON_LAYER1 else "tierC"
        else:
            continue
        ok = (got == expect)
        if not ok:
            fails.append(f"{r['id']} [{disp}] expected {expect} got {got} :: {r['text'][:50]!r}")

    # dedupe pair: g26 kept, g27 removed (identical after normalisation)
    g26, g27 = by_id["g26"]["text"], by_id["g27"]["text"]
    k26, k27 = filter_mod.dedupe_key(g26), filter_mod.dedupe_key(g27)
    if k26 is None or k26 != k27:
        fails.append(f"g26/g27 near-dupe NOT detected (keys: {k26!r} vs {k27!r})")

    total = len([r for r in rows if r["disposition"] != "drop_dupe"]) + 1
    if fails:
        print(f"GOLDEN TEST FAILED ({len(fails)}/{total}):")
        for f in fails:
            print("  [x]", f)
        return 1
    print(f"GOLDEN TEST PASSED -- {total}/{total} dispositions correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
