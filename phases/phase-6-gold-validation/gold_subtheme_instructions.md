# Discovery Sub-Theme Labeling — Instructions

These 50 reviews are all **discovery** reviews. Your job: decide which **codebook
sub-theme(s)** each one actually raises, so we can measure whether the codebook fits
the data — and whether it can answer the six questions. Label your own judgment; do
**NOT** open `gold_subtheme_key.json` (the model's predictions).

Open `gold_subtheme_sheet.csv` and fill the columns. ~25–35 min.

---

## The 11 sub-themes (+ `emerging`)

Tag each review with the **1–2 sub-themes it raises** (most raise one).

**Repetition (the bridge)**
| id | use when… |
|----|----|
| `repeat` | same songs on repeat, limited rotation, "plays the same stuff" |
| `shuffle` | shuffle isn't random / forced shuffle / "shuffle only" |
| `autoplay` | autoplay or auto-pick won't stop / switches to songs you didn't choose |

**Recommendation problems (Bucket 3 — Q2)**
| id | use when… |
|----|----|
| `safe` | recs too safe / too similar / stuck / filter bubble / not enough new |
| `mismatch` | irrelevant or wrong recommendations / wrong genre / unrelated suggestions |
| `pushy` | unwanted recs forced at you / AI recs dominate the UI / pushed content |

**Finding-new-music problems (Bucket 2 — Q1)**
| id | use when… |
|----|----|
| `control` | wants control over recs/playback / can't pick songs / wants to disable a feature |
| `freegate` | the **free tier** blocks discovery (shuffle-only, skip/selection limits) |
| `dj` | the **AI DJ** specifically (cuts songs, crashes, poor picks, missing, or praised) |
| `newmusic` | can't find/surface **new releases** / Release Radar broken / refresh broken |

**Positive**
| id | use when… |
|----|----|
| `love` | a **positive** discovery experience (Discover Weekly / Daily Mix / Wrapped / "finds anything" praise) |

**Escape hatch**
| id | use when… |
|----|----|
| `emerging` | it's genuinely about discovery but fits **none** of the 11 above |

## How to fill the columns

- **`your_subthemes`** — the id(s), lowercase, comma-separated. E.g. `shuffle` · `mismatch,pushy` · `love`
- **`repetition_type`** — *only* if you tagged `repeat`/`shuffle`/`autoplay`: is the repetition **`chosen`** (the user *wants* to replay — comfort/mood/intentional) or **`imposed`** (the app *forces* sameness against their wish)? Most are `imposed`.
- **`missing_theme`** — **important**: if none of the 11 fit, write a short phrase for what's missing. This is how you tell us the codebook has a gap.
- **`notes`** — optional (e.g. "could be control or freegate").

## What this measures
Overall + per-sub-theme accuracy, a sub-theme confusion matrix, the `chosen`/`imposed`
split, and — from your `missing_theme` notes — whether the codebook is complete enough
to answer Q1 (finding), Q2 (recommendations), and Q4 (repetition). If a theme keeps
getting mislabeled, that's the signal to fix the codebook before we report on it.
