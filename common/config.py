"""Central configuration for the Spotify Review Intelligence pipeline.

Everything that parameterises the build lives here so the tool is reusable:
point it at a different app / countries / window / taxonomy and re-run.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PHASES_DIR = ROOT / "phases"

for _d in (DATA_DIR, RAW_DIR, INTERIM_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Target app (Spotify). Change these three to re-target the tool.
# ---------------------------------------------------------------------------
APP_NAME = "Spotify"
ANDROID_APP_ID = "com.spotify.music"      # Google Play package name
IOS_APP_ID = "324684580"                   # App Store numeric id

# ---------------------------------------------------------------------------
# TWO INDEPENDENT TRACKS (the app-store feeds expose different depths):
#
#  ANDROID — deep-paginates, so we census-scrape a real 6-MONTH window across a
#  few large English markets. Supports problem-sizing + volume-over-time.
#
#  iOS — RSS hard-caps at 500/country; only high-volume markets keep 500 reviews
#  inside ~3 weeks. So iOS is a CURRENT SNAPSHOT across the markets the scout
#  found to be both recent (<=21d) and English (>=50%). mostrecent only
#  (mosthelpful is dropped: it spans ~8 years and skews the star mix).
# ---------------------------------------------------------------------------
LANG = "en"
NOW = datetime.now(timezone.utc)

ANDROID_COUNTRIES = ["us", "gb", "in"]
ANDROID_MONTHS = 6                      # deep-collect depth

# Determined empirically by scout_ios.py (span<=21d & english>=50%); re-run the
# scout to refresh. See data/interim/ios_country_scout.json.
IOS_COUNTRIES = ["us", "gb", "ca", "in", "au"]
IOS_SORT = "mostrecent"

# ---------------------------------------------------------------------------
# Sizing — ~2,000 substantive is a SATURATION REFERENCE, not a cap or gate.
# We deliberately over-collect; substantive volume floats with saturation.
# ---------------------------------------------------------------------------
SUBSTANTIVE_REFERENCE = 2000          # informational only; never used as a ceiling
SUBSTANTIVE_FLOOR = 1200              # lower gate: below this, widen collection
OVERCOLLECT_MULTIPLE = 3              # aim to pull >= this * reference raw reviews

# ---------------------------------------------------------------------------
# Collection politeness / robustness
# ---------------------------------------------------------------------------
REQUEST_DELAY_SEC = 1.2               # base pause between paged requests
MAX_RETRIES = 4
BACKOFF_BASE_SEC = 2.0
IOS_RSS_MAX_PAGES = 10                # Apple RSS hard cap (~50 reviews/page)
ANDROID_PAGE_SIZE = 200               # google-play-scraper batch size

# ---------------------------------------------------------------------------
# Filtering thresholds (Phase 2). Tuned against the golden set.
# ---------------------------------------------------------------------------
NEAR_DUPE_SIMILARITY = 92             # rapidfuzz token_set_ratio (0-100); >= is a dupe
LANGDETECT_MIN_CHARS = 3              # below this, language detection is unreliable

# ---------------------------------------------------------------------------
# Taxonomy — the six fixed top-level categories (+ 'other' catch-all).
# Order here is NOT display order (the dashboard sorts by count); colours
# match the design tokens / mock.
# ---------------------------------------------------------------------------
# 8 display categories. `playback`->`tech` (rename), `updates` added.
# Multi-label: a review may carry 1-3 of these. `none` (contentless) and
# `podcast` (podcast-only -> discarded, out of scope) are routing-only, not display.
CATEGORIES = [
    {"id": "discovery", "name": "Discovery & Recs",          "color": "#1DB954"},
    {"id": "tech",      "name": "Tech / Reliability",        "color": "#E5484D"},
    {"id": "ux",        "name": "UX / Navigation",           "color": "#3E63DD"},
    {"id": "pricing",   "name": "Pricing / Account / Ads",   "color": "#F5A623"},
    {"id": "catalogue", "name": "Catalogue / Availability",  "color": "#8E4EC6"},
    {"id": "audio",     "name": "Audio Quality",             "color": "#12A594"},
    {"id": "updates",   "name": "App Updates",               "color": "#D29922"},
    {"id": "other",     "name": "Other / Multiple",          "color": "#6B7280"},
]
CATEGORY_IDS = [c["id"] for c in CATEGORIES]

# ---------------------------------------------------------------------------
# Groq models (Phase 4/5). Verified live before the full run.
# ---------------------------------------------------------------------------
GROQ_MODEL_BROAD = "llama-3.1-8b-instant"   # Layer 1
GROQ_MODEL_DEEP = "openai/gpt-oss-120b"     # Layer 2 (highest quality)
GROQ_MODEL_DEEP_FAST = "openai/gpt-oss-20b"  # Layer 2 fallback — separate quota pool, faster, slightly lower quality
GROQ_API_KEY_ENV = "GROQ_API_KEY"


def groq_api_key() -> str | None:
    return os.environ.get(GROQ_API_KEY_ENV)


def groq_api_keys() -> list[str]:
    """All configured Groq keys, in priority order: GROQ_API_KEY, then
    GROQ_API_KEY_2..5. Multiple keys (separate accounts) are round-robined to
    multiply the free-tier daily token budget. De-duplicated, blanks dropped."""
    names = [GROQ_API_KEY_ENV] + [f"GROQ_API_KEY_{i}" for i in range(2, 6)]
    keys: list[str] = []
    for n in names:
        v = (os.environ.get(n) or "").strip()
        if v and v not in keys:
            keys.append(v)
    return keys
