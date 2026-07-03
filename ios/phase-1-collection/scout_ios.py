"""Phase 1 (iOS) — country scout.

The iOS track is a CURRENT snapshot, so a country only qualifies if its 500
most-recent reviews still fall within ~2-3 weeks (i.e. the market is high-volume
enough that 500 reviews == recent). Low-volume markets where 500 reviews reach
back months would pollute the "today" framing and are dropped.

Scope is English-only, so we also estimate each country's English share and keep
only countries that are both RECENT and English-yielding.

Writes data/interim/ios_country_scout.json and prints a table.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone

from common import config as C
from common.io import write_json
from common.logging_setup import get_logger

log = get_logger("phase1.scout_ios")

# Broad candidate set: English-official/common markets + major global markets
# (the latter to confirm we are not missing a high-volume English store and to
# show the volume landscape; non-English ones are reported but out of scope).
CANDIDATES = ["us", "gb", "ca", "au", "in", "ie", "nz", "sg", "ph", "za", "ng",
              "my", "pk", "ae", "hk", "br", "mx", "de", "fr", "es", "it", "id",
              "jp", "nl", "se"]

QUALIFY_DAYS = 21          # span must be <= this to count as "current"
MIN_ENGLISH_PCT = 50       # and English-yielding enough to be useful


def _english_pct(texts: list[str]) -> float:
    from langdetect import DetectorFactory, detect
    DetectorFactory.seed = 0
    en = tot = 0
    for t in texts:
        t = (t or "").strip()
        if len(t) < 20:
            continue
        tot += 1
        try:
            if detect(t) == "en":
                en += 1
        except Exception:  # noqa: BLE001
            pass
    return round(100 * en / tot, 0) if tot else 0.0


def scout_country(cc: str) -> dict:
    dates, texts = [], []
    for page in range(1, C.IOS_RSS_MAX_PAGES + 1):
        url = (f"https://itunes.apple.com/{cc}/rss/customerreviews/"
               f"page={page}/id={C.IOS_APP_ID}/sortby=mostrecent/json")
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                feed = json.load(resp).get("feed", {})
        except Exception:  # noqa: BLE001
            break
        ents = [e for e in feed.get("entry", []) if "im:rating" in e]
        if not ents:
            break
        for e in ents:
            d = e.get("updated", {}).get("label")
            if d:
                dates.append(d[:10])
            texts.append((e.get("title", {}).get("label", "") + " " +
                         (e.get("content", {}).get("label") or "")))
        time.sleep(0.2)
    if not dates:
        return {"country": cc, "count": 0, "span_days": None, "english_pct": 0,
                "qualifies": False}
    dates.sort()
    oldest = datetime.fromisoformat(dates[0] + "T00:00:00+00:00")
    span = (datetime.now(timezone.utc) - oldest).days
    eng = _english_pct(texts)
    qualifies = (len(dates) >= 450 and span <= QUALIFY_DAYS and eng >= MIN_ENGLISH_PCT)
    return {"country": cc, "count": len(dates), "oldest": dates[0],
            "span_days": span, "english_pct": eng, "qualifies": qualifies}


def run() -> dict:
    rows = []
    for cc in CANDIDATES:
        r = scout_country(cc)
        rows.append(r)
        log.info("%-3s count=%-4s span=%-5s days  english=%-4s%%  %s",
                 cc.upper(), r["count"], r["span_days"], r["english_pct"],
                 "QUALIFIES" if r["qualifies"] else "")
    rows.sort(key=lambda x: (not x["qualifies"], x["span_days"] if x["span_days"] else 9999))
    qualifiers = [r["country"] for r in rows if r["qualifies"]]
    out = {"qualify_days": QUALIFY_DAYS, "min_english_pct": MIN_ENGLISH_PCT,
           "rows": rows, "qualifiers": qualifiers}
    write_json(C.INTERIM_DIR / "ios_country_scout.json", out)
    print("\n  CC  | count | span(d) | eng% | qualifies")
    print("  ----+-------+---------+------+----------")
    for r in rows:
        print(f"  {r['country'].upper():3s} | {str(r['count']):>5s} | "
              f"{str(r['span_days']):>7s} | {str(int(r['english_pct'])):>4s} | "
              f"{'YES' if r['qualifies'] else ''}")
    print(f"\n  QUALIFIERS ({len(qualifiers)}): {', '.join(c.upper() for c in qualifiers)}")
    return out


if __name__ == "__main__":
    run()
