# Phase 5 — Discovery Codebook v3 (REVISED after the borderline-tightening test)

> Revised 2026-06-27 from a blind borderline re-label (22 reviews from the 4 fuzziest
> themes; user hand-labeled, scored against the v2 Claude codes). Two themes did not
> survive human review at all — **`autoplay` confirmed 0/6** (scattered into
> control/tech/repeat/mismatch) and **`safe` confirmed 0/6** (collapsed into `repeat`).
> `newmusic` held 5/6. v3 **removes `autoplay` and `safe`**, redistributes their
> reviews, and adds a **strict non-discovery gate** (the test also surfaced 3–4
> non-discovery reviews — incl. a German one — that should never have been in the pool).
>
> **This codebook is applied by the canonical model `gpt-oss-120b` over the FULL 1,792
> discovery pool in one consistent pass.** (v2 was a deadline Claude hand-code of 690.)

## Changes vs v2
1. **REMOVED `autoplay`.** It captured a heterogeneous pile humans split apart. Redistribute:
   - queue/autoplay that won't stop or **plays songs you didn't choose** → **`control`**
     (loss of control over playback; this is the project's headline "loss of control" theme);
   - if it's the **same songs** looping → add **`repeat`**;
   - if it's a genuine **malfunction / glitch** (app misbehaving, not a discovery/control
     grievance) → **drop as `not_discovery`**.
2. **REMOVED `safe`.** It collapsed into `repeat`. Redistribute:
   - "same songs / limited rotation / stale recs" (recs recur) → **`repeat`**;
   - "no **new** releases / can't surface new music" → **`newmusic`**;
   - "recs are **wrong** / off-target" → **`mismatch`**;
   - "**make** recs better / more diverse" (constructive) → **`smartrec`**.
3. **STRICT discovery gate** (was "default to true"). A review enters the inventory ONLY
   with a clear, substantive discovery/recommendation/playback-control angle. **Precision
   over recall** — a clean inventory beats catching every borderline case.
4. **Deterministic language guard** (pre-model): non-English reviews are dropped before
   coding (catches the German leak the lenient Phase-2 filter let through).

## The 10 themes (down from 12)
| id | group | bucket | use when… |
|----|-------|--------|----|
| `repeat` | repetition | bridge | same songs on repeat, limited rotation, stale/recurring recs |
| `shuffle` | repetition | bridge | shuffle isn't random / forced shuffle / "shuffle only" |
| `mismatch` | relevance | recs | irrelevant/wrong recs, wrong genre, unrelated suggestions |
| `pushy` | relevance | recs | unwanted recs forced at you, AI recs dominate, pushed content |
| `smartrec` | relevance | recs | **constructive** ask for smarter/more personalized recs or a discovery feature |
| `control` | features | finding | can't pick songs / no rec control / queue or autoplay plays songs you didn't choose / wants to disable a feature |
| `freegate` | features | finding | free tier blocks discovery (shuffle-only, skip/selection limits) |
| `dj` | features | finding | AI DJ **problem** (cuts songs, crashes, poor picks, missing) |
| `newmusic` | features | finding | can't surface NEW releases / Release Radar / refresh broken |
| `love` | positive | — | positive discovery experience (incl. praising DJ/Discover Weekly/Wrapped) |
| `emerging` | features | finding(emerging) | genuinely discovery but fits none above — **use sparingly** |

`autoplay` and `safe` are **retired** — the coder must never output them; any stray
output is remapped (`autoplay`→`control`, `safe`→`repeat`).

## Co-tag rules (carried from v2, plus the v3 redistributions)
- **Free-tier forced shuffle** ("shuffle always on", shuffle-only on free) → **`shuffle` + `freegate`**.
- **Queue / autoplay you can't stop or steer** → **`control`** (+ `repeat` if same songs).
- **Positive feature praise** (DJ, Smart Shuffle, Discover Weekly, Wrapped) → **`love`**
  (add the feature theme only if a *problem* is also raised).
- **Constructive "make recs better"** → **`smartrec`** (not a bare staleness complaint, which is `repeat`).

## STRICT non-discovery gate (the guardrail) → drop from the inventory
Set `discovery: false` (DROP) when the review is ONLY about, with no real discovery angle:
- ads / price / subscription cost **without** a playback-control angle;
- a crash / bug / login / offline / device (e.g. car/Bluetooth) error;
- sound / audio quality;
- a specific song or artist simply **missing** from the catalogue;
- podcasts / audiobooks;
- generic praise or insult with no mention of recommendations or what plays;
- **non-English** text (also caught deterministically before coding).

When genuinely unsure, or the discovery angle is a single passing word with no substance,
**drop it**. Three independent guards enforce this: (1) a deterministic language filter,
(2) the strict model gate above, (3) `not_discovery` records are excluded from the inventory.

## Repetition bridge (now `repeat` + `shuffle` only)
With `autoplay` retired, the repetition cluster is **`repeat` + `shuffle`**. Each carries a
`chosen` vs `imposed` tag; real data is ~100% imposed → the dashboard reframes the bridge as
"repetition is overwhelmingly app-imposed."
