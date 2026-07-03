# Borderline sub-theme test — labeling rubric

You're re-labeling 22 reviews drawn from the 4 fuzziest discovery themes
(`autoplay`, `safe`, `newmusic`, `other/emerging`) so we can see where the Claude
re-code over/under-applied them. **The sheet does not show the original labels** — mark
each review on its own merits, then we score against the originals.

## How to fill the sheet (`data/interim/borderline_sheet.csv`)
- **`your_themes`** — 1–3 theme ids, comma-separated (e.g. `autoplay,control`).
- **`your_repetition_type`** — only for `repeat`/`shuffle`/`autoplay`: `chosen` (user *wants*
  the replay) or `imposed` (app forces it). Most are `imposed`.
- **`notes`** — optional (e.g. "could be safe or smartrec").
- If a review isn't really about discovery (pure ads/price/crash/sound/missing song, or
  generic praise), use **`not_discovery`**.

## The 12 themes (+ routing labels)
| id | use when… |
|----|----|
| `repeat` | same songs on repeat, limited rotation |
| `shuffle` | shuffle isn't random / forced shuffle |
| `autoplay` | autoplay/queue won't stop, plays songs you didn't choose |
| `safe` | recs too safe/similar/stale/filter-bubble (a **complaint**) |
| `mismatch` | irrelevant/wrong recs, wrong genre, unrelated suggestions |
| `pushy` | unwanted recs forced at you, AI recs dominate |
| `smartrec` | **asks** for smarter/more personalized recs or a discovery feature |
| `control` | wants to choose/disable, can't pick songs, no rec control |
| `freegate` | free tier blocks discovery (shuffle-only, skip/selection limits) |
| `dj` | AI DJ **problem** (cuts songs, crashes, poor picks, missing) |
| `newmusic` | can't surface NEW releases / Release Radar / refresh broken |
| `love` | positive discovery experience (incl. praising DJ/Discover Weekly/Wrapped) |
| `emerging` | genuinely discovery but fits none above |
| `not_discovery` | not about discovery at all → drop |

## The boundaries that bleed (decide deliberately)
- **`autoplay` vs `shuffle` vs `repeat`** — autoplay = the *queue keeps going / plays things
  you didn't pick*; shuffle = *order isn't random*; repeat = *same songs recur*. Add `control`
  if they explicitly want to choose/disable.
- **`safe` vs `smartrec`** — `safe` = bare **complaint** recs are stale/too similar; `smartrec`
  = **constructive** ask to make recs better / add a feature.
- **`newmusic` vs `safe`** — `newmusic` = can't see **new releases** (Release Radar, refresh
  broken); `safe` = recs exist but feel stale/repetitive.
- **`emerging` vs `not_discovery`** — `emerging` = real discovery angle that fits nothing else;
  `not_discovery` = no discovery angle at all.

After labeling, run:
`python -m phases.phase-5-layer2-discovery.borderline_test score`
