"""Phase 3 (Android track) — volume-over-time & window.

Census stats over the Android 6-month corpus: monthly review volume, monthly
avg star rating, and distinct app-version cycles spanned. These are EXACT
(census, not sampled). The discovery-share overlay on the trend is filled later
(needs Layer-1 categorisation, Phase 4) — here we lay the temporal backbone and
the monthly strata the LLM sample will draw from.

iOS has no equivalent (it is a ~2-3 week snapshot) — this phase is Android only.

Output: data/interim/android_window.json
"""
from __future__ import annotations

from collections import defaultdict

from common import config as C
from common.io import read_jsonl, write_json
from common.logging_setup import get_logger

log = get_logger("phase3.window")

MONTH_NAMES = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May",
               "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct",
               "11": "Nov", "12": "Dec"}


def _major_minor(v: str | None) -> str | None:
    if not v:
        return None
    parts = str(v).split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else parts[0]


def run() -> dict:
    adir = C.INTERIM_DIR / "android"
    # baseline population = all English reviews (substantive candidates + Tier C)
    rows = list(read_jsonl(adir / "substantive_candidates.jsonl")) + \
        list(read_jsonl(adir / "tierC.jsonl"))
    log.info("loaded %d english android reviews", len(rows))

    by_month_ratings: dict[str, list[int]] = defaultdict(list)
    by_month_strata: dict[str, list[str]] = defaultdict(list)  # review_ids per month (sampling frame)
    versions: set[str] = set()
    for r in rows:
        mk = (r.get("date") or "unknown")[:7]
        if isinstance(r.get("rating"), int):
            by_month_ratings[mk].append(r["rating"])
        by_month_strata[mk].append(r["review_id"])
        mm = _major_minor(r.get("app_version"))
        if mm:
            versions.add(mm)

    months = sorted(m for m in by_month_ratings if m != "unknown")
    trends = []
    for m in months:
        ratings = by_month_ratings[m]
        yr, mo = m.split("-")
        trends.append({
            "month": MONTH_NAMES.get(mo, m),
            "monthKey": m,
            "reviews": len(by_month_strata[m]),
            "avgRating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "discoveryPct": None,   # filled post-Phase-4
        })

    app_updates = len(versions)
    win = f"{trends[0]['month']} {months[0][:4]} - {trends[-1]['month']} {months[-1][:4]}" \
        if trends else "n/a"
    justification = (
        f"Android census over {len(months)} calendar months "
        f"({win}); {len(rows):,} English reviews spanning {app_updates} distinct "
        f"app-version cycles. Census-scraped in full (not a sorted slice), so monthly "
        f"volume and star averages are exact and month-stratified LLM sampling is valid. "
        f"iOS is reported separately as a current snapshot (store feed exposes only ~2-3 weeks)."
    )

    out = {
        "track": "android",
        "window": {"collection": win, "analysis": win, "appUpdates": app_updates,
                   "justification": justification},
        "trends": trends,
        "strata_counts": {m: len(by_month_strata[m]) for m in months},
        "unknown_month": len(by_month_strata.get("unknown", [])),
    }
    write_json(C.INTERIM_DIR / "android_window.json", out)
    log.info("window=%s  appUpdates=%d  months=%d", win, app_updates, len(months))
    for t in trends:
        log.info("  %s %s: %d reviews, avg %.2f", t["monthKey"], t["month"],
                 t["reviews"], t["avgRating"] or 0)
    return out


if __name__ == "__main__":
    run()
