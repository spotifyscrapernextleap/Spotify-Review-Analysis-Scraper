# Gold-Set Labeling — Instructions (please read once before starting)

You are creating the **ground truth** we measure the classifier against. Your labels
must be **your own judgment** — please do **NOT** open `gold_key.json` (that file holds
the model's predictions; looking would invalidate the test).

**What to do:** open `gold_labeling_sheet.csv` (in Excel / Google Sheets) and fill the
three blank columns for each of the 50 rows. ~20–30 min.

---

## The 8 categories (+ `none`)

Tag each review with the **1–3 categories it actually raises**. Most raise just **one**.

| id | use it when the review is about… |
|----|----|
| `discovery` | recommendations (Discover Weekly / Daily Mix / Release Radar), the algorithm, taste-matching, **smart shuffle / autoplay / AI DJ picking songs**, **shuffle not being random**, **"same songs again" / repetition**, finding new music, or wanting control over what gets played/recommended |
| `tech` | crashes, freezing, bugs, lag, songs stopping/skipping, playback failing, offline/download problems, connectivity, casting (Sonos/smart speakers), **login / account errors** ("something went wrong") |
| `ux` | interface, layout, design, **search usability**, settings, playlist organisation, widgets, lockscreen controls, interface feature requests |
| `pricing` | price, subscription, billing, family plan, account access — **and ALWAYS ads / "too many ads" / ad length** (ads always go here) |
| `catalogue` | **availability only** — a specific song/album/artist is **missing** or greyed-out, regional restrictions, missing lyrics (NOT the wrong song playing) |
| `audio` | **sound quality only** — bitrate, clarity, "quality fades in/out", equalizer, volume |
| `updates` | the review is about a **recent app update / new version** ("the new update", "since the update"). **Additive** — also tag the affected category, e.g. `updates,tech` |
| `other` | a clear, specific product claim that fits none of the above |
| `none` | **no specific claim** — pure praise, insult, or noise ("best app ever", "love it", "trash"). Use `none`, not `other`, for vague positivity |

## A few rules (the same ones the taxonomy uses)

1. **Ads → always `pricing`** (never tech/catalogue).
2. **`none` for vague praise/insult** with no specific claim (not `other`).
3. **Praise + complaint:** label the **complaint** (the issue the review raises), not the praise.
4. **Updates is additive:** include `updates` *plus* the real category it affects.
5. Some rows are deliberately **tricky borderline cases** (short-but-pointed, or long-but-empty). Label what's actually there — don't overthink.

## How to fill the columns

- **`label_categories`** — the category id(s), lowercase, comma-separated. Examples: `discovery` · `pricing,tech` · `none` · `updates,ux`
- **`label_sentiment`** — overall tone: `positive`, `negative`, or `mixed`
- **`notes`** — optional (e.g. "could be ux or discovery")

When you're done, save the CSV and tell me — I'll compute accuracy, per-category
breakdown, Cohen's kappa, the confusion matrix, and abstention calibration from your labels.
