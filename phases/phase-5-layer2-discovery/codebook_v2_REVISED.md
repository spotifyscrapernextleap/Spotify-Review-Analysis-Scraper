# Phase 5 — Discovery Codebook v2 (REVISED after gold-set validation)

> Revised 2026-06-26 from the user's sub-theme gold-set labeling (48 scored: 73%
> ≥1-theme overlap, 60% model-primary-in-truth, but boundary fuzz + a ~10% gap).
> Changes are targeted: one new theme, explicit co-tag rules for the fuzzy
> boundaries, up to 3 labels, and one definition tightening. **This is the codebook
> Claude applies in the deadline re-code; the canonical model stays gpt-oss-120b.**

## Changes vs v1
1. **NEW theme `smartrec`** (group: relevance → Bucket 3) — **constructive** requests
   for smarter / more personalized recommendations or a discovery feature
   ("suggest more by my taste", "add a My Vibe mode", "give me a thumbs-down").
   This is the ~10% the gold set found dumped into `emerging`/`safe`. It is the
   *forward-looking* sibling of `safe`: `safe` = complains recs are stale; `smartrec`
   = asks for them to be better.
2. **`dj` is now problems-only.** Positive DJ mentions → `love` (+`dj` only if a DJ
   problem is also raised). Removes the love↔dj overlap the gold set hit.
3. **Up to 3 themes** (was 2) — the gold set showed real reviews raise more than 2.
4. **Co-tag rules** for the fuzzy boundaries (below).

## The 12 themes
| id | group | bucket | use when… |
|----|-------|--------|----|
| `repeat` | repetition | bridge | same songs on repeat, limited rotation |
| `shuffle` | repetition | bridge | shuffle isn't random / forced shuffle |
| `autoplay` | repetition | bridge | autoplay/queue won't stop, plays songs you didn't choose |
| `safe` | relevance | recs | recs too safe/similar/stale/filter-bubble (a **complaint**) |
| `mismatch` | relevance | recs | irrelevant/wrong recs, wrong genre, unrelated suggestions |
| `pushy` | relevance | recs | unwanted recs forced at you, AI recs dominate |
| `smartrec` | relevance | recs | **NEW** — asks for smarter/more personalized recs or a discovery feature |
| `control` | features | finding | wants to choose/disable, can't pick songs, no rec control |
| `freegate` | features | finding | free tier blocks discovery (shuffle-only, skip/selection limits) |
| `dj` | features | finding | AI DJ **problem** (cuts songs, crashes, poor picks, missing) |
| `newmusic` | features | finding | can't surface NEW releases / Release Radar / refresh broken |
| `love` | positive | — | positive discovery experience (incl. praising DJ / Discover Weekly / Wrapped) |
| `emerging` | features | finding(emerging) | genuinely discovery but fits none above |

## Co-tag rules (the gold-set boundary fixes)
- **Free-tier forced shuffle** ("shuffle is always on", "can't turn off shuffle", shuffle-only on free) → tag **`shuffle` + `freegate`**.
- **Queue / autoplay you can't stop or steer** ("stop the queue", "won't stop playing", "plays songs I didn't pick") → **`autoplay`**, and add **`control`** if they explicitly want to choose/disable.
- **Positive feature praise** (DJ, Smart Shuffle, Discover Weekly, Wrapped) → **`love`** (add the feature theme only if a *problem* is also raised).
- **Constructive "make recs better"** → **`smartrec`** (not `safe`, which is the bare complaint).

## Not-discovery (abstain → drop from the pool)
Reviews that are purely ads/price/billing, a crash/login bug, sound quality, a
missing song, or generic praise with no discovery angle. (The gold set also caught
a **non-English review** that leaked the English filter — flag, don't code.)

## Repetition bridge (unchanged decision)
`repeat`/`shuffle`/`autoplay` carry a `chosen` vs `imposed` tag. Real data is ~100%
imposed → the dashboard reframes the bridge as "repetition is overwhelmingly
app-imposed."
