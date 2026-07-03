# Phase 5 — Discovery Codebook (DRAFT — awaiting user sign-off)

> Built from open-coding 200 stratified Android discovery reviews (105 raw codes →
> 11 sub-themes). **Counts below are indicative from the sample only** — the real
> per-theme counts come from closed-coding all 2,359 discovery reviews against this
> locked codebook (step 3). This draft fixes the STRUCTURE: sub-themes, their
> `group`, the Bucket-2/Bucket-3 mapping, and the chosen-vs-imposed bridge.
>
> **Open-coding finding:** 64/200 (32%) of 8B-tagged discovery reviews had NO real
> discovery content (ads/price/crash mis-tags). Closed-coding will abstain on these
> (→ `emerging`/non-discovery), so they don't inflate discovery numbers.

## Sub-themes (→ `discovery.themes`)

| id | name | group | Bucket | indicative n | definition (verbatim triggers) |
|----|------|-------|--------|----|----|
| `repeat` | Same songs on repeat | repetition | bridge | 13 | "plays the same songs again", limited rotation |
| `shuffle` | Shuffle isn't random | repetition | bridge | 20 | shuffle not random, forced shuffle, "shuffle only" |
| `autoplay` | Autoplay forces songs | repetition | bridge | 16 | autoplay/auto-pick won't stop, switches to unwanted songs |
| `safe` | Recs too safe / filter bubble | relevance | recs (B3) | 7 | recs too similar / history-based / "stuck", filter bubble |
| `mismatch` | Irrelevant / wrong recs | relevance | recs (B3) | 10 | wrong genre, unrelated suggestions, "recs are bad" |
| `pushy` | Unwanted recs pushed | relevance | recs (B3) | 9 | AI recs forced on free tier, recs dominate the UI |
| `control` | No control over recs/playback | features | finding (B2) | ~9 | wants to pick songs, no rec control, can't choose |
| `freegate` | Free tier blocks discovery | features | finding (B2) | ~6 | shuffle-only/skip/selection limits gate discovery |
| `dj` | AI DJ problems | features | finding (B2) | 7 | AI DJ cuts songs / crashes / poor picks / missing |
| `newmusic` | Can't surface new releases | features | finding (B2) | 7 | new releases hidden, Release Radar broken, refresh broken |
| `love` | Discovery that delights | positive | — | 49 | Discover Weekly/Daily Mix/Wrapped praise, "finds anything" |

*(`control` + `freegate` were merged as 15 in the indicative count; split here as distinct sub-themes.)*

## Repetition cluster (→ `discovery.repetitionCluster`)
`themeIds = [repeat, shuffle, autoplay]` — the bridge centrepiece (~49 sample mentions).

## The bridge: chosen vs imposed (→ `bridge`)
The same observed behaviour ("users hear the same music repeatedly") splits two ways:
- **CHOSEN** — comfort/intentional replay, mood/habit looping → *a need, not a fault* → flows into **unmet needs**.
- **IMPOSED** — shuffle that isn't random, autoplay forcing, filter-bubble sameness → *a discovery/rec failure* → flows into **Buckets 2 & 3**.

The closed-coding pass will tag each `repeat`/`shuffle`/`autoplay` review as chosen vs imposed to populate the two branches with real counts.

## Buckets (→ `buckets`)
- **Bucket 2 — Problems finding new music** (`finding`): `control`, `freegate`, `dj`, `newmusic` + `emerging`.
- **Bucket 3 — Problems with the recommendation system** (`recs`): `safe`, `mismatch`, `pushy` + `emerging`.

## Bucket 1 — Listening behaviours (→ `behaviors`)
Surfaced thinly so far (workout/focus/sleep/background/mood). Open-coding will be
extended to extract disclosed use-contexts during closed-coding (exploratory).

## Open questions for sign-off
1. Keep `control` and `freegate` **separate**, or merge into one "free-tier control" theme?
2. Is `dj` (AI DJ) a **finding** problem (B2) or its own thing? Currently B2/features.
3. Bridge: confirm chosen-vs-imposed is the right framing for `repeat` (vs treating all repetition as imposed).
4. Anything in the 105 raw codes (`data/interim/phase5_opencode_codes.json`) you want promoted to its own sub-theme?
