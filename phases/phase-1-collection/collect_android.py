"""Phase 1 (Android track) — deep 6-month census scrape.

Google Play deep-paginates, so we collect the FULL population back ~6 months
for each English market. Census-scraping the whole window (not a sorted slice)
is what makes later month-stratified sampling statistically valid.

ROBUSTNESS (after an OOM on the first attempt):
- **Streams each country to disk page-by-page** (data/raw/android/{cc}.jsonl) and
  keeps only counts in memory — no multi-hundred-k list in RAM.
- **Per-country `.done.json` sidecar** → a completed country is skipped on re-run,
  so a crash never wipes finished work (true resumability, EC-2/EC-37).
- **Per-request thread timeout** so a hung network call can't stall forever.
- Final step stream-merges the per-country files into android_raw.jsonl.

Output:
  data/raw/android/{cc}.jsonl + {cc}.done.json
  data/raw/android_raw.jsonl        (merged)
  data/raw/android_manifest.json    (counts by country x month)
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import defaultdict
from datetime import timedelta, timezone

from common import config as C
from common.io import read_json, write_json
from common.logging_setup import get_logger

log = get_logger("phase1.android")
CUTOFF = C.NOW - timedelta(days=int(C.ANDROID_MONTHS * 30.5))
SAFETY_CAP = 250_000
FETCH_TIMEOUT = 90  # seconds per page request
ADIR = C.RAW_DIR / "android"


def _rid(country: str, raw_id, text: str) -> str:
    if raw_id:
        return f"android:{country}:{raw_id}"
    h = hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:16]
    return f"android:{country}:{h}"


def _major_minor(v) -> str | None:
    if not v:
        return None
    p = str(v).split(".")
    return ".".join(p[:2]) if len(p) >= 2 else p[0]


def _fetch(country: str, token):
    """One page with retries + a hard thread timeout. Returns (batch, token) or
    (None, None) on exhaustion/timeout."""
    from google_play_scraper import Sort, reviews

    for attempt in range(C.MAX_RETRIES):
        box: dict = {}

        def worker():
            try:
                box["v"] = reviews(C.ANDROID_APP_ID, lang=C.LANG, country=country,
                                   sort=Sort.NEWEST, count=C.ANDROID_PAGE_SIZE,
                                   continuation_token=token)
            except Exception as e:  # noqa: BLE001
                box["e"] = e

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join(FETCH_TIMEOUT)
        if t.is_alive():
            log.warning("android %s page hung > %ds (attempt %d)", country, FETCH_TIMEOUT, attempt)
        elif "v" in box:
            return box["v"]
        else:
            log.warning("android %s err: %s", country, box.get("e"))
        time.sleep(C.BACKOFF_BASE_SEC * (2 ** attempt))
    return (None, None)


def collect_country(country: str, max_pages: int = 0) -> dict:
    sidecar = ADIR / f"{country}.done.json"
    if sidecar.exists():
        info = read_json(sidecar)
        log.info("android %s: already complete (%d) — skipping", country, info["count"])
        return info

    out_path = ADIR / f"{country}.jsonl"
    token = None
    count = 0
    pages = 0
    status = "complete"
    by_month: dict[str, int] = defaultdict(int)
    versions: set[str] = set()

    with open(out_path, "w", encoding="utf-8") as fh:
        while count < SAFETY_CAP and (not max_pages or pages < max_pages):
            batch, token = _fetch(country, token)
            if batch is None:
                status = "partial:fetch_failed"
                break
            if not batch:
                break
            reached = False
            for r in batch:
                at = r.get("at")
                if at and at.replace(tzinfo=timezone.utc) < CUTOFF:
                    reached = True
                    continue
                date_iso = at.replace(tzinfo=timezone.utc).isoformat() if at else None
                rec = {
                    "review_id": _rid(country, r.get("reviewId"), r.get("content", "")),
                    "store": "android", "country": country,
                    "rating": r.get("score"),
                    "text": r.get("content") or "",
                    "title": None, "date": date_iso,
                    "app_version": r.get("reviewCreatedVersion"),
                    "thumbs_up": r.get("thumbsUpCount"),
                    "fetched_at": C.NOW.isoformat(),
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
                by_month[(date_iso or "unknown")[:7]] += 1
                mm = _major_minor(r.get("app_version"))
                if mm:
                    versions.add(mm)
            pages += 1
            if pages % 25 == 0:
                fh.flush()
                log.info("  android %s: %d (page %d)", country, count, pages)
            if reached or token is None:
                break
            time.sleep(C.REQUEST_DELAY_SEC)

    info = {"country": country, "count": count, "pages": pages, "status": status,
            "by_month": dict(by_month), "versions": sorted(versions)}
    write_json(sidecar, info)
    log.info("android %s: %d reviews (%d pages, %s) -> saved", country, count, pages, status)
    return info


def run(countries: list[str] | None = None, max_pages: int = 0) -> dict:
    countries = countries or C.ANDROID_COUNTRIES
    ADIR.mkdir(parents=True, exist_ok=True)
    manifest = {"track": "android", "cutoff": CUTOFF.isoformat(), "now": C.NOW.isoformat(),
                "countries": countries, "months": C.ANDROID_MONTHS,
                "by_country": {}, "by_country_month": {}}
    total = 0
    for cc in countries:
        info = collect_country(cc, max_pages=max_pages)
        total += info["count"]
        manifest["by_country"][cc] = {"count": info["count"], "status": info["status"]}
        manifest["by_country_month"][cc] = info["by_month"]

    # stream-merge per-country files -> android_raw.jsonl (memory-safe)
    merged = C.RAW_DIR / "android_raw.jsonl"
    with open(merged, "w", encoding="utf-8") as out:
        for cc in countries:
            p = ADIR / f"{cc}.jsonl"
            if p.exists():
                with open(p, encoding="utf-8") as fh:
                    for line in fh:
                        out.write(line)
    manifest["total"] = total
    write_json(C.RAW_DIR / "android_manifest.json", manifest)
    log.info("ANDROID DONE total=%d across %s", total, countries)
    return manifest


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--countries", default="", help="comma list override, e.g. us,gb,in")
    p.add_argument("--max-pages", type=int, default=0, help="cap pages/country (0=full; for smoke test)")
    a = p.parse_args()
    ccs = [c.strip() for c in a.countries.split(",") if c.strip()] or None
    run(countries=ccs, max_pages=a.max_pages)
