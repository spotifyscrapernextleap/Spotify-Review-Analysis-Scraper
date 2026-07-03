# iOS Discovery Sub-Theme Labeling — Instructions (codebook v3)

These ~25 reviews are all **iOS** reviews the deep-coder tagged as **discovery**. Your job:
decide which **codebook sub-theme(s)** each one actually raises, so we can measure whether the
v3 codebook fits the iOS data. Label your own judgment; do **NOT** open
`gold_subtheme_key_ios.json` (the model's predictions).

Open `gold_subtheme_sheet_ios.csv` and fill the columns. ~15–20 min.

> This is codebook **v3** — `autoplay` and `safe` were retired (autoplay folded into
> `control`; safe split across `repeat`/`newmusic`/`mismatch`/`smartrec`), and `smartrec` is a
> live theme. There are **10 themes** (+ `emerging`), not 11.

---

## The 10 sub-themes (+ `emerging`)

Tag each review with the **1–2 sub-themes it raises** (most raise one).

**Repetition (the bridge)**
| id | use when… |
|----|----|
| `repeat` | same songs on repeat, limited rotation, "plays the same stuff", stale recs |
| `shuffle` | shuffle isn't random / forced shuffle / "shuffle only" |

**Recommendation problems**
| id | use when… |
|----|----|
| `mismatch` | irrelevant or wrong recommendations / wrong genre / unrelated suggestions |
| `pushy` | unwanted recs forced at you / AI recs dominate the UI / pushed content |
| `smartrec` | a **constructive request** for smarter / more personalized recs or a discovery feature |

**Finding / control problems**
| id | use when… |
|----|----|
| `control` | wants control over what plays or is recommended / can't pick songs / queue or autoplay plays songs you didn't choose / wants to disable a feature |
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
| `emerging` | it's genuinely about discovery but fits **none** of the 10 above |

## How to fill the columns

- **`your_subthemes`** — the id(s), lowercase, comma-separated. E.g. `shuffle` · `mismatch,pushy` · `love`
  - If the review turns out **not** to be about discovery at all (a pure ads/crash/catalogue
    review that leaked in), leave this blank and note why in `missing_theme` (e.g. "not
    discovery — crash"). Those rows are scored separately as model false-positives.
- **`repetition_type`** — *only* if you tagged `repeat`/`shuffle`: is the repetition **`chosen`**
  (the user *wants* to replay — comfort/mood/intentional) or **`imposed`** (the app *forces*
  sameness against their wish)? Most are `imposed`.
- **`missing_theme`** — **important**: if none of the 10 fit, write a short phrase for what's
  missing (or "not discovery" as above). This is how you tell us the codebook has a gap.
- **`notes`** — optional (e.g. "could be control or freegate").

## What this measures
Overall + per-sub-theme accuracy on iOS data, a sub-theme confusion matrix, the
`chosen`/`imposed` split, and — from your `missing_theme` notes — whether the v3 codebook
travels cleanly from Android to iOS. Because the sheet is only ~25 reviews, treat the numbers
as a **systematic-miscoding check** (is a theme collapsing into the wrong bucket?) rather than
a precise per-theme accuracy figure.
