"""Phase 2 — Normalisation & deterministic filtering (the guardrails).

No model is involved here. Reviews are ROUTED, never deleted: every review
participates in whatever analysis its content supports. Order:

  1. Field integrity   — validate rating/date/country/text; quarantine + COUNT
                          malformed records (never coerce, EC-9).
  2. Deduplicate        — exact + near-duplicate (word-set fingerprint, EC-10).
  3. Language filter    — drop confident non-English; SHORT texts bypass
                          detection (protects short English from langdetect
                          false-drops, EC-8); Latin+English-token fallback keeps
                          Hinglish/slang.
  4. Junk / tier route  — emoji-only, char-repeat, single-sentiment, spam, and
                          empty text -> Tier C (contentless: counted, star kept,
                          never sent to a model). Everything else -> SUBSTANTIVE
                          CANDIDATE (final Tier A/B split rides on Layer-1
                          categorisation in Phase 4).

Outputs:
  data/interim/substantive_candidates.jsonl
  data/interim/tierC.jsonl
  data/interim/quarantined.jsonl
  data/interim/filter_report.json   (funnel + field integrity + dedupe/lang counts)
"""
from __future__ import annotations

import re
from collections import Counter

from common import config as C
from common.io import read_jsonl, read_json, write_json, write_jsonl
from common.logging_setup import get_logger

log = get_logger("phase2.filter")

# --- junk lexicons ---------------------------------------------------------
SENTIMENT_WORDS = {
    "good", "bad", "nice", "ok", "okay", "great", "awful", "amazing", "perfect",
    "love", "hate", "trash", "garbage", "best", "worst", "cool", "fine", "meh",
    "wow", "excellent", "terrible", "fantastic", "horrible", "awesome", "sucks",
    "useless", "rubbish", "brilliant", "lovely", "wonderful", "superb",
}
FILLER_WORDS = {"it", "this", "the", "is", "app", "ever", "very", "so", "really",
                "a", "an", "im", "i", "u", "my", "for", "of", "to", "and"}
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF←-⇿⬀-⯿️‍]+"
)
URL_RE = re.compile(r"(https?://|www\.|\b\w+\.(?:com|net|ly|io|gg|co)\b)", re.I)
SPAM_RE = re.compile(r"\b(free followers|visit now|click here|promo code|gift card|"
                     r"redeem|crypto|telegram|whatsapp \+?\d)\b", re.I)
WORD_RE = re.compile(r"[a-z0-9']+")
ENGLISH_TOKENS = {"the", "is", "and", "not", "so", "my", "this", "it", "are", "on",
                  "of", "to", "for", "you", "with", "but", "have", "just", "they",
                  "what", "why", "now", "same", "songs", "music", "app", "fix",
                  "please", "pls", "want", "cant", "dont", "wont", "no", "every"}


def _norm_text(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def dedupe_key(t: str) -> str | None:
    """Punctuation-stripped, whitespace-collapsed, lowercased text — used as the
    near-dupe key. Returns None for SHORT reviews (< 8 words): identical short
    text ("good", "love it") is almost always separate ratings, not reposts, and
    collapsing them would corrupt the star baseline. Only longer reviews, where
    identical text strongly implies a repost (incl. cross-country), are deduped.
    Catches case/punctuation/spacing variants (EC-10 — conservative)."""
    norm = re.sub(r"[^a-z0-9 ]", " ", _norm_text(t))
    norm = re.sub(r"\s+", " ", norm).strip()
    words = norm.split()
    if len(words) < 8:
        return None
    return norm


# ---------------------------------------------------------------------------
# 1. Field integrity
# ---------------------------------------------------------------------------
def field_integrity(rec: dict) -> tuple[dict | None, str | None]:
    """Return (clean_record, None) or (None, quarantine_reason). Never coerces."""
    rating = rec.get("rating")
    if not (isinstance(rating, int) and 1 <= rating <= 5):
        return None, "rating"
    date = rec.get("date")
    if not date or not isinstance(date, str):
        return None, "date"
    if not rec.get("country"):
        return None, "country"
    # text may legitimately be empty (Tier C) — that is NOT a quarantine reason.
    rec["text"] = rec.get("text") or ""
    return rec, None


# ---------------------------------------------------------------------------
# 3. Language
# ---------------------------------------------------------------------------
def is_english(text: str) -> bool:
    """True if English (or English-parseable code-switch).

    langdetect is unreliable under ~20 chars, so SHORT texts are decided by
    script alone (predominantly Latin -> treat as English; junk routing then
    handles any contentless ones). Texts with no letters at all (emoji/punct)
    return True so junk routing — not the language filter — catches them.
    Longer non-English passages are dropped, with a Latin+English-token
    fallback that deliberately KEEPS Hinglish/slang (the false-keep the eval
    layer later quantifies, EC-8)."""
    from langdetect import DetectorFactory, detect
    DetectorFactory.seed = 0
    stripped = EMOJI_RE.sub("", text).strip()
    letters = sum(ch.isalpha() for ch in stripped)
    if letters == 0:
        return True  # no language signal — let junk routing decide
    ascii_letters = sum(ch.isascii() and ch.isalpha() for ch in stripped)
    latin_ratio = ascii_letters / letters
    words = WORD_RE.findall(stripped.lower())
    if len(stripped) < 20 or len(words) < 4:
        return latin_ratio >= 0.8  # too short for langdetect — script decides
    try:
        if detect(stripped) == "en":
            return True
    except Exception:  # noqa: BLE001
        pass
    # Latin-script + >=2 common English tokens -> keep (Hinglish/slang).
    return latin_ratio >= 0.8 and len(set(words) & ENGLISH_TOKENS) >= 2


# ---------------------------------------------------------------------------
# 4. Junk / contentless routing
# ---------------------------------------------------------------------------
def junk_reason(text: str) -> str | None:
    """Return a Tier-C reason if contentless/junk, else None."""
    t = text.strip()
    if not t:
        return "empty"
    if SPAM_RE.search(t) or URL_RE.search(t):
        return "spam"
    no_emoji = EMOJI_RE.sub("", t)
    if not re.search(r"[A-Za-z0-9]", no_emoji):
        return "emoji_only"
    # repeated-character string (e.g. "aaaaaa", "!!!!!")
    if re.fullmatch(r"(.)\1{4,}", re.sub(r"\s", "", t)):
        return "char_repeat"
    words = WORD_RE.findall(t.lower())
    if len(words) <= 1:
        return "single_word"
    if len(words) <= 3 and all(w in SENTIMENT_WORDS | FILLER_WORDS for w in words):
        return "sentiment_only"
    return None


def classify_text(text: str) -> str:
    """Text-level disposition for golden-set testing — mirrors the run order
    (language filter, then junk/tier routing):
    'nonenglish' | 'tierC' | 'substantive_candidate'."""
    if not is_english(text):
        return "nonenglish"
    if junk_reason(text):
        return "tierC"
    return "substantive_candidate"


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------
def run(track: str) -> dict:
    """Filter one track independently. track in {'android','ios'}."""
    assert track in ("android", "ios"), track
    out_dir = C.INTERIM_DIR / track
    manifest = read_json(C.RAW_DIR / f"{track}_manifest.json")
    raw = list(read_jsonl(C.RAW_DIR / f"{track}_raw.jsonl"))
    collected = len(raw)
    log.info("[%s] loaded %d raw reviews", track, collected)

    # 1. field integrity
    clean, quarantined = [], []
    qcounter: Counter = Counter()
    for rec in raw:
        ok, reason = field_integrity(rec)
        if ok:
            clean.append(ok)
        else:
            qcounter[reason] += 1
            rec["_quarantine_reason"] = reason
            quarantined.append(rec)
    log.info("field integrity: %d clean, %d quarantined %s",
             len(clean), len(quarantined), dict(qcounter))

    # 2a. EXACT dedupe by underlying store reviewId (review_id = "store:cc:id").
    #     This collapses the Android cross-"country" triplication: google-play's
    #     country param does NOT segment reviews — all 3 pulls return the same
    #     global review set (same reviewId). Must run before text-dedupe so SHORT
    #     duplicated reviews are also collapsed (they would otherwise 3x-inflate
    #     the star baseline). iOS reviewIds are genuinely per-storefront, so this
    #     removes ~0 there.
    def _uid(rid: str) -> str:
        p = rid.split(":", 2)
        return p[2] if len(p) == 3 else rid

    seen_id: set[str] = set()
    id_deduped, n_id_dupes = [], 0
    for rec in clean:
        u = _uid(rec["review_id"])
        if u in seen_id:
            n_id_dupes += 1
            continue
        seen_id.add(u)
        if track == "android":
            rec["country"] = "global"  # Android country is not a real dimension
        id_deduped.append(rec)
    log.info("[%s] id-dedupe: removed %d (same reviewId across pulls), kept %d",
             track, n_id_dupes, len(id_deduped))

    # 2b. text near-dedupe — conservative: collapse >=8-word reviews identical
    #     after normalisation (genuine reposts with a different id). Short ratings
    #     are never deduped (separate baseline data points).
    seen = set()
    deduped, n_text_dupes = [], 0
    for rec in id_deduped:
        k = dedupe_key(rec["text"])
        if k is not None and k in seen:
            n_text_dupes += 1
            continue
        if k is not None:
            seen.add(k)
        deduped.append(rec)
    n_dupes = n_id_dupes + n_text_dupes
    log.info("[%s] text-dedupe: removed %d, kept %d (total deduped %d)",
             track, n_text_dupes, len(deduped), n_dupes)

    # 3. language filter
    english, n_nonenglish = [], 0
    for rec in deduped:
        if is_english(rec["text"]):
            english.append(rec)
        else:
            n_nonenglish += 1
    log.info("language: dropped %d non-English, kept %d", n_nonenglish, len(english))

    # 4. junk / tier routing
    candidates, tierC = [], []
    creason: Counter = Counter()
    for rec in english:
        jr = junk_reason(rec["text"])
        if jr:
            rec["tier"] = "C"
            rec["tierC_reason"] = jr
            creason[jr] += 1
            tierC.append(rec)
        else:
            rec["tier"] = "AB_candidate"
            candidates.append(rec)
    log.info("tiering: %d substantive candidates, %d Tier C %s",
             len(candidates), len(tierC), dict(creason))

    write_jsonl(out_dir / "substantive_candidates.jsonl", candidates)
    write_jsonl(out_dir / "tierC.jsonl", tierC)
    write_jsonl(out_dir / "quarantined.jsonl", quarantined)

    # field integrity report (per field % valid + count quarantined) for the eval layer
    fields = ["rating", "date", "country", "text"]
    field_integrity_report = []
    for fld in fields:
        q = qcounter.get(fld, 0)
        valid_pct = round(100 * (collected - q) / collected, 1) if collected else 100.0
        field_integrity_report.append({"field": fld, "valid": valid_pct, "quarantined": q})

    report = {
        "funnel": {
            "collected": collected,
            "deduplicated": len(deduped),
            "english": len(english),
            "tierC": len(tierC),
            "substantive_candidates": len(candidates),
            # tierA / tierB / substantive / discoveryAll / deepCoded -> Phase 4+
        },
        "removed": {
            "quarantined": len(quarantined), "duplicates": n_dupes,
            "id_duplicates": n_id_dupes, "text_duplicates": n_text_dupes,
            "non_english": n_nonenglish,
        },
        "quarantine_by_field": dict(qcounter),
        "tierC_by_reason": dict(creason),
        "field_integrity": field_integrity_report,
        "manifest_collected": manifest.get("total"),
        "track": track,
    }
    write_json(C.INTERIM_DIR / f"{track}_filter_report.json", report)

    # EC-22 funnel reconciliation check (deterministic steps)
    assert collected == len(deduped) + n_dupes + len(quarantined), "dedupe step leak"
    assert len(deduped) == len(english) + n_nonenglish, "language step leak"
    assert len(english) == len(candidates) + len(tierC), "tier step leak"
    log.info("[%s] funnel reconciles OK  collected=%d -> candidates=%d tierC=%d",
             track, collected, len(candidates), len(tierC))
    return report


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("track", choices=["android", "ios"])
    run(p.parse_args().track)
