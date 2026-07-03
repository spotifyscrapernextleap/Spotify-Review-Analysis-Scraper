"""Phase 1 (iOS track) — current-snapshot scrape.

iTunes RSS hard-caps at ~10 pages x 50 = 500/country, so iOS is a CURRENT
snapshot, not a time series. We pull `mostrecent` only (mosthelpful is dropped:
it spans ~8 years and skews the star mix) across the markets the scout found to
be both recent and English (config.IOS_COUNTRIES).

Output:
  data/raw/ios_raw.jsonl
  data/raw/ios_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone

from common import config as C
from common.io import write_json, write_jsonl
from common.logging_setup import get_logger

log = get_logger("phase1.ios")


def _rid(country: str, raw_id, text: str) -> str:
    if raw_id:
        return f"ios:{country}:{raw_id}"
    h = hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:16]
    return f"ios:{country}:{h}"


def collect_country(country: str) -> tuple[list[dict], str]:
    out: list[dict] = []
    status = "complete"
    for page in range(1, C.IOS_RSS_MAX_PAGES + 1):
        url = (f"https://itunes.apple.com/{country}/rss/customerreviews/"
               f"page={page}/id={C.IOS_APP_ID}/sortby={C.IOS_SORT}/json")
        entries = None
        for attempt in range(C.MAX_RETRIES):
            try:
                with urllib.request.urlopen(url, timeout=25) as resp:
                    entries = [e for e in json.load(resp).get("feed", {}).get("entry", [])
                               if "im:rating" in e]
                break
            except Exception as e:  # noqa: BLE001
                wait = C.BACKOFF_BASE_SEC * (2 ** attempt)
                log.warning("ios %s p%d err (%s); backoff %.1fs", country, page, e, wait)
                time.sleep(wait)
        if entries is None:
            status = "partial:retries_exhausted"
            break
        if not entries:
            break
        for e in entries:
            text = e.get("content", {}).get("label") or ""
            rating = e.get("im:rating", {}).get("label")
            out.append({
                "review_id": _rid(country, e.get("id", {}).get("label"), text),
                "store": "ios", "country": country,
                "rating": int(rating) if rating and rating.isdigit() else rating,
                "text": text,
                "title": e.get("title", {}).get("label"),
                "date": e.get("updated", {}).get("label"),
                "app_version": e.get("im:version", {}).get("label"),
                "thumbs_up": None,
                "fetched_at": C.NOW.isoformat(),
            })
        time.sleep(C.REQUEST_DELAY_SEC)
    log.info("ios %s: %d reviews (%s)", country, len(out), status)
    return out, status


def run() -> dict:
    all_rows = []
    manifest = {"track": "ios", "sort": C.IOS_SORT, "now": C.NOW.isoformat(),
                "countries": C.IOS_COUNTRIES, "by_country": {}}
    for cc in C.IOS_COUNTRIES:
        rows, status = collect_country(cc)
        all_rows += rows
        spans = sorted((r["date"] or "")[:10] for r in rows if r["date"])
        manifest["by_country"][cc] = {
            "count": len(rows), "status": status,
            "oldest": spans[0] if spans else None,
            "newest": spans[-1] if spans else None,
        }
    write_jsonl(C.RAW_DIR / "ios_raw.jsonl", all_rows)
    manifest["total"] = len(all_rows)
    write_json(C.RAW_DIR / "ios_manifest.json", manifest)
    log.info("iOS DONE total=%d across %s", len(all_rows), C.IOS_COUNTRIES)
    return manifest


if __name__ == "__main__":
    run()
