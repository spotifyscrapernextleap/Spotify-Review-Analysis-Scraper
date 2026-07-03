"""The binding interface: pydantic models for `window.REVIEW_DATA`.

This is the schema the dashboard consumes (see `build and design docs/README.md`
Data Contract). The pipeline's final job (Phase 7) is to emit JSON that validates
against `ReviewData` here. Field names match the JSON keys EXACTLY (camelCase),
so a validated model dumps straight to the contract shape.

Run `python -m common.contract <snapshot.json>` to validate a snapshot file.

Golden rule enforced informally elsewhere: every percentage carries its raw `n`.
"""
from __future__ import annotations

import json
import sys
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    # Ignore unknown keys (e.g. the vestigial `crosswalk` in the mock) rather
    # than reject them, but validate everything we DO know about strictly.
    model_config = ConfigDict(extra="ignore")


# ---- funnel ---------------------------------------------------------------
class Funnel(_Base):
    collected: int
    deduplicated: int
    english: int
    tierA: int
    tierB: int
    tierC: int
    substantive: int          # == tierA + tierB
    discoveryAll: int
    deepCoded: int


# ---- window ---------------------------------------------------------------
class Window(_Base):
    collection: str
    analysis: str
    appUpdates: int
    justification: str


# ---- platforms ------------------------------------------------------------
class PlatformStat(_Base):
    count: int
    avgRating: float


class Platforms(_Base):
    ios: PlatformStat
    android: PlatformStat


# ---- baseline -------------------------------------------------------------
class StarRow(_Base):
    stars: int
    pct: float
    count: int


class Baseline(_Base):
    totalReviews: int
    avgRating: float
    distribution: List[StarRow]


# ---- categories -----------------------------------------------------------
class Category(_Base):
    id: str
    name: str
    count: int
    pct: float
    avgRating: float
    color: str


# ---- effect ---------------------------------------------------------------
class Effect(_Base):
    gap: float
    ciLow: float
    ciHigh: float
    note: str


# ---- trends ---------------------------------------------------------------
class TrendPoint(_Base):
    month: str
    reviews: int
    discoveryPct: float


class TrendDirection(_Base):
    label: str
    summary: str


# ---- discovery ------------------------------------------------------------
ThemeGroup = Literal["repetition", "relevance", "features", "positive"]


class Theme(_Base):
    id: str
    name: str
    count: int
    pct: float
    sentiment: float
    group: ThemeGroup


class RepetitionCluster(_Base):
    themeIds: List[str]
    totalCount: int
    pctOfDiscovery: float


class Discovery(_Base):
    totalMentions: int
    deepCoded: int
    avgRating: float
    effectSize: float
    themes: List[Theme]
    repetitionCluster: RepetitionCluster


# ---- buckets --------------------------------------------------------------
class Bucket(_Base):
    ids: List[str]
    emerging: int


class Buckets(_Base):
    finding: Bucket
    recs: Bucket


# ---- bridge ---------------------------------------------------------------
class NamedCount(_Base):
    name: str
    count: int


class BridgeBranch(_Base):
    total: int
    label: str
    sub: str
    flowsTo: str
    items: List[NamedCount]


class Bridge(_Base):
    total: int
    chosen: BridgeBranch
    imposed: BridgeBranch


# ---- behaviours / needs / segments ---------------------------------------
class Behavior(_Base):
    name: str
    mentions: int


Strength = Literal["strong", "moderate", "emerging"]


class UnmetNeed(_Base):
    need: str
    mentions: int
    strength: Strength


class Segment(_Base):
    name: str
    size: int          # % of sample; UI flags < 20 as low-n
    topTheme: str
    avgRating: float
    discoveryPct: float


# ---- delight / sentiment split -------------------------------------------
class DelightCategory(_Base):
    name: str
    pct: float


class Delight(_Base):
    positiveShare: float
    positiveCount: int
    byCategory: List[DelightCategory]
    topThemes: List[NamedCount]


class SentimentSplit(_Base):
    id: str
    name: str
    pos: float
    neg: float


# ---- quotes ---------------------------------------------------------------
class Quote(_Base):
    text: str
    rating: int
    platform: str
    store: str


# ---- validation -----------------------------------------------------------
class Validation(_Base):
    goldSetSize: int
    overallAccuracy: float
    categoryAccuracy: float
    themeAccuracy: float
    kappa: float


# ---- evaluation -----------------------------------------------------------
class SamplingBar(_Base):
    stars: int
    collected: float
    store: float


class Sampling(_Base):
    bars: List[SamplingBar]
    note: str


class FunnelReconcileRow(_Base):
    step: str
    inN: Optional[int]
    removed: Optional[int]
    reason: str
    outN: int


class FieldIntegrity(_Base):
    field: str
    valid: float
    quarantined: int


class LanguageCheck(_Base):
    falseDrop: float
    falseKeep: float
    example: str
    exampleVerdict: str


class Confusion(_Base):
    labels: List[str]
    matrix: List[List[float]]
    discoveryAccuracy: float


class GoldCoverage(_Base):
    cat: str
    count: int


class GoldComposition(_Base):
    total: int
    borderline: int
    easy: int
    coverage: List[GoldCoverage]


class Abstention(_Base):
    confidentShare: float
    confidentAccuracy: float
    abstainedShare: float
    abstainedAccuracy: float


class Evaluation(_Base):
    sampling: Sampling
    funnelReconcile: List[FunnelReconcileRow]
    fieldIntegrity: List[FieldIntegrity]
    languageCheck: LanguageCheck
    confusion: Confusion
    goldComposition: GoldComposition
    abstention: Abstention


# ---- root -----------------------------------------------------------------
class ReviewData(_Base):
    funnel: Funnel
    window: Window
    platforms: Optional[Platforms] = None
    baseline: Baseline
    categories: List[Category]
    effect: Effect
    trends: List[TrendPoint]
    trendDirection: TrendDirection
    discovery: Discovery
    buckets: Buckets
    bridge: Bridge
    behaviors: List[Behavior]
    unmetNeeds: List[UnmetNeed]
    segments: List[Segment]
    delight: Delight
    sentimentSplit: List[SentimentSplit]
    positiveDiscoveryThemes: List[NamedCount]
    quotes: Dict[str, List[Quote]]
    validation: Validation
    limitations: List[str]
    evaluation: Evaluation


def validate_snapshot(obj: dict) -> ReviewData:
    """Validate a dict against the contract. Raises pydantic.ValidationError."""
    return ReviewData.model_validate(obj)


def cross_checks(data: ReviewData) -> List[str]:
    """Contract-consistency checks beyond field types. Returns a list of
    human-readable problems (empty == clean). These catch the bugs that
    types alone miss (EC-17, EC-22, EC-24)."""
    problems: List[str] = []

    f = data.funnel
    if f.substantive != f.tierA + f.tierB:
        problems.append(f"funnel.substantive ({f.substantive}) != tierA+tierB ({f.tierA + f.tierB})")

    # every bucket id must exist in discovery.themes (EC-17)
    theme_ids = {t.id for t in data.discovery.themes}
    for bname, b in (("finding", data.buckets.finding), ("recs", data.buckets.recs)):
        for tid in b.ids:
            if tid not in theme_ids:
                problems.append(f"buckets.{bname} references unknown theme id '{tid}'")

    # repetition cluster ids must exist
    for tid in data.discovery.repetitionCluster.themeIds:
        if tid not in theme_ids:
            problems.append(f"repetitionCluster references unknown theme id '{tid}'")

    # quotes keys should be discovery theme ids
    for qid in data.quotes:
        if qid not in theme_ids:
            problems.append(f"quotes has key '{qid}' not in discovery.themes")

    # baseline distribution should sum ~100%
    pct_sum = sum(r.pct for r in data.baseline.distribution)
    if not (98 <= pct_sum <= 102):
        problems.append(f"baseline.distribution pct sums to {pct_sum}, expected ~100")

    return problems


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m common.contract <snapshot.json>")
        sys.exit(2)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    data = validate_snapshot(raw)
    issues = cross_checks(data)
    if issues:
        print("CONTRACT CROSS-CHECK FAILURES:")
        for i in issues:
            print("  -", i)
        sys.exit(1)
    print(f"OK: {path} validates against the contract and passes cross-checks.")
