# Handoff: Spotify Review Intelligence Dashboard

## Overview

This package is the design reference for a **review-intelligence dashboard** that turns scraped
Spotify app-store reviews into a narrative the reader can trust: it sizes the music-discovery
problem against every other complaint, shows the balanced picture (problems *and* delight), goes
deep on the discovery diagnosis, lets anyone check the raw evidence, and exposes a full evaluation
layer so the machinery underneath can be audited.

The narrative spine, in one line:
**size the problem → show it's not the whole story → go deep on discovery → let anyone check the evidence → show the work.**

You are building the scraper now. The most important thing in this package for you is the
**[Data Contract](#data-contract-the-scraper--dashboard-interface)** — the exact shape of the JSON
the dashboard consumes. If your scraper/analysis pipeline emits that object, the dashboard renders
with zero changes. Treat that schema as the interface between the two halves of the project.

---

## About the Design Files

The files in this bundle are **design references created in HTML** — a working prototype showing the
intended look, structure, and behaviour. They are **not production code to copy directly.**

Your task is to **recreate this design in your target codebase's environment** (React, Vue, Svelte,
etc.) using its established component patterns, charting libraries, and styling system. If no
front-end environment exists yet, pick the most appropriate framework for the project and implement
there. The HTML/inline-style approach used in the prototype is a prototyping convenience, **not** a
recommendation for production — use a real charting library (Recharts, Visx, ECharts, D3, etc.) and a
real component structure.

### What's in this bundle

| File | What it is |
|------|------------|
| `Review Intelligence Dashboard (visualiser).html` | **Open this in any browser.** Self-contained, offline visualiser of the full prototype — the source of truth for look & behaviour. |
| `dashboard-design-spec.md` | The original content/narrative spec. Explains *why* each section exists. |
| `source/V5 Atlas.dc.html` | The prototype source (markup + render logic). Reference only. |
| `source/data.js` | **The data contract.** The mock `window.REVIEW_DATA` object — the schema your scraper must produce. |
| `source/support.js` | Prototype runtime. Not relevant to production; ignore. |

---

## Fidelity

**High-fidelity.** Final colours, typography, spacing, and layout are all intentional and specified
below. Recreate the UI to match — using your codebase's libraries to achieve the same result. The
**data is mock** (plausible but fabricated); only the *shape* of the data is real and binding.

---

## Data Contract (the scraper → dashboard interface)

The dashboard reads a single global object, `window.REVIEW_DATA`. Your pipeline's job is to produce
this object (as JSON / an API response). Every field below maps to something rendered on screen.
**Counts and percentages are passed in pre-computed — the dashboard does no analysis, only display.**

> **Golden rule from the spec:** *a percentage without an `n` is not a finding.* Every share/percent
> field has a corresponding raw count somewhere in the object. Keep them together.

```jsonc
{
  // ---- Collection funnel: one count per pipeline stage ----
  "funnel": {
    "collected": 4832,        // raw reviews pulled
    "deduplicated": 3891,     // after exact + near-dupe removal
    "english": 3412,          // after language filter
    "tierA": 1847,            // deep-codeable (rich text)
    "tierB": 892,             // thin but categorisable
    "tierC": 673,             // star-rating only / contentless
    "substantive": 2739,      // tierA + tierB
    "discoveryAll": 479,      // substantive reviews mentioning discovery
    "deepCoded": 412          // discovery reviews coded against the sub-theme codebook
  },

  // ---- Analysis window justification ----
  "window": {
    "collection": "Jun 2025 – Jun 2026",
    "analysis": "Dec 2025 – Jun 2026",
    "appUpdates": 4,
    "justification": "string — why this window was chosen"
  },

  "platforms": {                                   // optional context
    "ios":     { "count": 1706, "avgRating": 3.1 },
    "android": { "count": 1706, "avgRating": 3.3 }
  },

  // ---- Star baseline (least-biased sentiment signal) ----
  "baseline": {
    "totalReviews": 3412,
    "avgRating": 3.2,
    "distribution": [                              // one row per star, 1..5
      { "stars": 1, "pct": 28, "count": 955 }
      // ...
    ]
  },

  // ---- Share of voice across the six+ categories ----
  // Order = display order. Highlight whichever id === "discovery".
  "categories": [
    { "id": "discovery", "name": "Discovery & Recs", "count": 479,
      "pct": 17.5, "avgRating": 2.4, "color": "#1DB954" }
    // playback, ux, pricing, catalogue, audio, other ...
  ],

  // ---- Effect size with confidence interval (the headline number) ----
  "effect": {
    "gap": -0.8, "ciLow": -1.0, "ciHigh": -0.6,
    "note": "string — e.g. 'The interval excludes zero...'"
  },

  // ---- Discovery share of voice over time (line chart) ----
  "trends": [
    { "month": "Dec", "reviews": 312, "discoveryPct": 16.2 }
    // ... one per month in the analysis window
  ],
  "trendDirection": { "label": "Flat", "summary": "string read-out of the direction" },

  // ---- Discovery deep-dive ----
  "discovery": {
    "totalMentions": 479,
    "deepCoded": 412,
    "avgRating": 2.4,
    "effectSize": -0.8,
    "themes": [                                    // the consolidated sub-themes
      { "id": "repeat", "name": "Same songs on repeat", "count": 89,
        "pct": 21.6, "sentiment": 1.9, "group": "repetition" }
      // group ∈ "repetition" | "relevance" | "features" | "positive"
      // "group":"repetition" rows are visually highlighted as the cluster.
    ],
    "repetitionCluster": {
      "themeIds": ["repeat", "bubble", "shuffle", "safe"],
      "totalCount": 225, "pctOfDiscovery": 54.6
    }
  },

  // ---- Bucket assignment for the 3-bucket narrative (locked Iteration A) ----
  // Maps theme ids into the two PROBLEM buckets. "emerging" = escape-hatch count.
  "buckets": {
    "finding": { "ids": ["stale","safe","bubble","control"], "emerging": 12 }, // Bucket 2
    "recs":    { "ids": ["mismatch","repeat","shuffle","context"], "emerging": 9 } // Bucket 3
  },

  // ---- The repetition bridge: same behaviour, two readings ----
  "bridge": {
    "total": 225,
    "chosen":  { "total": 83,  "label": "CHOSEN repetition",  "sub": "A need, not a fault",
                 "flowsTo": "Flows into unmet needs",
                 "items": [ { "name": "Comfort listening", "count": 38 } /* ... */ ] },
    "imposed": { "total": 142, "label": "IMPOSED repetition", "sub": "A discovery / rec failure",
                 "flowsTo": "Flows into Buckets 2 & 3",
                 "items": [ { "name": "Filter bubble", "count": 56 } /* ... */ ] }
  },

  // ---- Bucket 1: disclosed listening behaviours (exploratory) ----
  "behaviors": [ { "name": "Background listening (work / study)", "mentions": 89 } /* ... */ ],

  // ---- Independent read 1: unmet needs (ranked, flat) ----
  "unmetNeeds": [ { "need": "string", "mentions": 64, "strength": "strong" } /* ... */ ],
  // strength ∈ "strong" | "moderate" | "emerging"

  // ---- Independent read 2: use-case segments (exploratory, low-n flagged) ----
  "segments": [ { "name": "Active Explorers", "size": 28, "topTheme": "Filter bubble",
                  "avgRating": 2.1, "discoveryPct": 31 } /* ... */ ],
  // "size" is % of sample; the UI flags size < 20 as "directional, low n".

  // ---- 1B Delight counterweight (deliberately light) ----
  "delight": {
    "positiveShare": 31, "positiveCount": 849,
    "byCategory": [ { "name": "Catalogue / Availability", "pct": 58 } /* ... */ ],
    "topThemes": [ { "name": "string", "count": 142 } /* ... */ ]
  },

  // ---- 1C Sentiment split per category (pos vs neg share) ----
  "sentimentSplit": [ { "id": "discovery", "name": "Discovery & Recs", "pos": 22, "neg": 78 } /* ... */ ],
  "positiveDiscoveryThemes": [ { "name": "string", "count": 41 } /* ... */ ],

  // ---- Evidence Explorer: quotes keyed by discovery sub-theme id ----
  "quotes": {
    "repeat": [
      { "text": "the exact review snippet that justified the tag",
        "rating": 1, "platform": "iOS", "store": "US" }
      // ...
    ]
    // one array per theme id in discovery.themes
  },

  // ---- Methodology ----
  "validation": { "goldSetSize": 50, "overallAccuracy": 84, "categoryAccuracy": 88,
                  "themeAccuracy": 79, "kappa": 0.72 },
  "limitations": [ "plain-language limitation string", /* ... */ ],

  // ---- 4B Evaluation layer (the audit) ----
  "evaluation": {
    "sampling": {                                  // collected vs store-reported star dist
      "bars": [ { "stars": 1, "collected": 28, "store": 21 } /* ...1..5 */ ],
      "note": "string stating the gap"
    },
    "funnelReconcile": [                            // in = out + removed, per step
      { "step": "Deduplicated", "inN": 4832, "removed": 941, "reason": "exact + near-duplicate", "outN": 3891 }
      // first row may have inN/removed = null (the start)
    ],
    "fieldIntegrity": [ { "field": "Rating", "valid": 99.4, "quarantined": 21 } /* ... */ ],
    "languageCheck": {
      "falseDrop": 1.8, "falseKeep": 2.3,
      "example": "a code-switched / Hinglish review string",
      "exampleVerdict": "string — why it was kept/dropped"
    },
    "confusion": {                                 // gold-set confusion matrix
      "labels": ["Playback","Discovery","UX","Pricing","Catalogue","Audio"],
      "matrix": [ [91,2,3,1,1,2], /* rows = truth, cols = predicted, % */ ],
      "discoveryAccuracy": 86
    },
    "goldComposition": {
      "total": 50, "borderline": 32, "easy": 18,
      "coverage": [ { "cat": "Discovery", "count": 11 } /* ... */ ]
    },
    "abstention": { "confidentShare": 82, "confidentAccuracy": 89,
                    "abstainedShare": 18, "abstainedAccuracy": 61 }
  }
}
```

### Derived values the dashboard computes (you do NOT need to send these)

- Bar widths / heights (normalised against the max in each group).
- The deep-dive **buckets** read their themes out of `discovery.themes` by id — send each sub-theme
  once in `discovery.themes`; `buckets` only references ids.
- Confidence-interval label string `95% CI [−1.0, −0.6]` is formatted from `effect`.
- Evidence sentiment label (Positive/Negative) is derived from each quote's `rating` (≥3 = positive).

---

## Screens / Views

The app is a **fixed-sidebar dashboard**: a 236px left nav with four sections, and a scrolling main
content pane (max-width 1080px). Selecting a nav item swaps the main pane (single-page, client-side;
no route reload required, but real routes are fine).

### Nav (sidebar)
- Fixed, full height, 236px wide. Background `#090c10`, 1px right border `#21262d`.
- Brand block: eyebrow "REVIEW INTELLIGENCE" (10px/600, `#1DB954`, letter-spacing 2px, uppercase) +
  subtitle "Spotify · Discovery Analysis" (`#484f58`).
- Four items: **Overview · Discovery Deep Dive · Evidence Explorer · Methodology & Evaluation.**
  Active item: white text, `rgba(29,185,84,0.08)` background, 3px left border `#1DB954`. Inactive:
  `#8b949e`, transparent.
- Footer: "Prototype · Mock Data" + date range (replace with real provenance).

### 1 · Overview  ("Summary")
Purpose: make three things true before the reader goes anywhere — discovery is real, sized, and not
the whole story.
- **Hero row**: three equal cells in a 1px-gap grid (hairline-divided card). (a) Discovery share of
  voice `17.5%` (white); (b) Effect size `−0.8★` (`#f85149`) with CI subtitle; (c) Positive share
  `31%` (`#1DB954`). 40px/700 numbers, `-0.04em` tracking.
- **Caveat note**: green-tinted callout about unprompted mentions / undercounting.
- **Share of voice by category**: sorted horizontal bars; discovery bar green (`#1DB954`), others
  `#30363d`; each row shows `pct% (n=…)` and avg rating. Label `pct% (n=479)`.
- **Rating comparison**: card with two bars (All reviews 3.2★ grey, Discovery 2.4★ green) + the
  `−0.8 stars` headline, and the interpretation note.
- **Rating distribution**: 1–5★ histogram (baseline). Bars red (≤2★), amber (3★), green (≥4★);
  show pct on top, `n=` below.
- **Discovery share over time**: line chart (green line + faint area fill) with a direction read-out
  ("Flat — …"). In production use a real line chart; the prototype hand-builds an SVG polyline.
- **Delight counterweight** (light pass): positive-share-by-category mini bars + top delight themes
  list. Tagged "Light pass".
- **Sentiment in context**: per-category diverging bar (green positive / red negative), discovery
  highlighted; plus positive-discovery theme chips. Closes with a "Next →" handoff note.

### 2 · Discovery Deep Dive
Purpose: the primary investigation, told as a **three-bucket narrative** (this is the **locked**
design — there is no view toggle).
- **Bucket 1 — Listening behaviour** (numbered badge 1, blue): 2-col grid of disclosed behaviours
  with mention counts. Tagged "Exploratory".
- **The repetition bridge**: centred framing quote "Users listen to the same music repeatedly"
  ({total} reviews) splitting into two cards — **CHOSEN** (green, "a need, not a fault") and
  **IMPOSED** (red, "a discovery/rec failure") — each listing its sub-items with counts and a
  "↳ flows into…" line. This is the narrative hinge; keep the two-branch split explicit.
- **Bucket 2 — Problems finding new music** (badge 2, red): ranked bars + "emerging / other" line.
- **Bucket 3 — Problems with the recommendation system** (badge 3, red): ranked bars + emerging line.
- **Two independent reads** (below a divider): **Unmet needs** (ranked list with strength pills:
  strong=green, moderate=amber, emerging=grey) and **Use-case segments** (cards; size<20 flagged
  "directional, low n"). These are flat reads of the same pool — *not* slices of the buckets.
- Each element carries a quiet `↳ addresses Q…` tag (`#3a4350`, near-invisible) — the deliberately
  invisible question crosswalk. There is **no** crosswalk section/tab.

### 3 · Evidence Explorer
Purpose: the receipts layer. A skeptic pulls any thread and checks it against raw text.
- **Filter bar**: Sentiment (All/Positive/Negative), Platform (All/iOS/Android), Country
  (All/US/UK/CA/AU/IN) as chip toggles. Active chip green-tinted.
- **Left rail**: selectable list of discovery sub-themes with review counts.
- **Quote cards**: each shows the snippet (italic), a theme tag, sentiment label (green/red), star
  string, and `platform · country`. Left border colour = sentiment. Empty state when filters exclude
  everything. Header shows "{shown} of {total} quotes".

### 4 · Methodology & Evaluation
Two layers. Methodology is always visible; the evaluation layer expands inline beneath it.
- **Methodology (visible)**: collection funnel (bars + per-step removed counts in red); gold-set
  agreement headline (84%); analysis-window justification card; denominators card; "how the sentiment
  baseline is computed" card; limitations (2-col, red bullets).
- **The expander**: a centred pill — **"Wondering if the data is reliable? Here's how. ▼"** (green
  outline, rounded 30px). Clicking it expands the evaluation layer **inline below** (it does not
  navigate away); chevron flips to ▲.
- **Evaluation layer (revealed)**, the 7 audit visuals, in order:
  1. **Sampling fairness** — collected vs store-reported star distribution (paired bars) + gap note.
  2. **Funnel reconciliation** — table proving `in = out + removed` at each step.
  3. **Field integrity** — 5 stat cards (% valid + count quarantined per field).
  4. **Language-filter spot-check** — false-drop / false-keep rates + a worked code-switched example.
  5. **Per-category accuracy** — confusion matrix heatmap (rows=truth, cols=predicted), Discovery
     row/col highlighted, standalone discovery accuracy called out. *The centrepiece.*
  6. **Gold-set composition** — borderline-vs-easy split bar + per-category coverage bars.
  7. **Abstention calibration** — confident-labels accuracy vs abstained accuracy (paired).
  Closes with the narrative-close statement.

---

## Interactions & Behavior

- **Section nav**: click swaps main pane. State: `activeSection ∈ {overview, discovery, evidence, methodology}`.
- **Evaluation expander**: boolean `evalOpen`; toggles the evaluation block inline. Reveal animates
  in (`atlasReveal`: opacity 0→1, translateY 8px→0, 0.4s ease). Default collapsed.
- **Evidence filters**: `selectedTheme` (sub-theme id), `evSentiment`, `evPlatform`, `evCountry`.
  Quotes = `quotes[selectedTheme]` filtered by the three chip filters. Sentiment derived from rating
  (≥3 positive). Show an empty state when the filtered set is empty.
- **Bars/charts**: animate width/height on mount (`transition: width/height 0.4–0.5s`).
- All copy in the prototype is final unless your data says otherwise.

## State Management

| State | Type | Default | Drives |
|-------|------|---------|--------|
| `activeSection` | enum | `overview` | which view is shown |
| `evalOpen` | boolean | `false` | evaluation layer visibility (Methodology) |
| `selectedTheme` | string (theme id) | `repeat` | Evidence quote list |
| `evSentiment` | `all\|pos\|neg` | `all` | Evidence filter |
| `evPlatform` | `all\|iOS\|Android` | `all` | Evidence filter |
| `evCountry` | `all\|US\|UK\|CA\|AU` | `all` | Evidence filter |

Data fetching: load `REVIEW_DATA` once (single fetch / SSR prop). No per-interaction fetching — all
views read from the one object. Render an empty/loading state until it resolves.

---

## Design Tokens

**Type** — Sora (Google Fonts), weights 400/500/600/700. Page titles 24px/700 (`-0.02em`); section
headers 14–20px/600–700; eyebrows 10px/600 uppercase (`letter-spacing 1.5px`); body 12–13px; big
metrics 40–48px/700 (`-0.04em`); micro-labels 10–11px.

**Colour**

| Token | Hex | Use |
|-------|-----|-----|
| Background | `#0d1117` | page |
| Surface | `#161b22` | cards |
| Surface deep | `#0f1318` | bridge / nested panels |
| Sidebar | `#090c10` | nav |
| Border | `#21262d` | hairlines, card borders |
| Border subtle | `#30363d` | empty bar tracks |
| Text primary | `#c9d1d9` | body |
| Text bright | `#e6edf3` / `#fff` | headings / emphasis |
| Text secondary | `#8b949e` | sub-copy |
| Text muted | `#484f58` | captions |
| Text ghost | `#3a4350` | the quiet "↳ addresses Q…" tags |
| **Accent (green)** | `#1DB954` | discovery highlight, positive, primary accent |
| Negative (red) | `#f85149` | effect size, negative sentiment, problem buckets |
| Warning (amber) | `#d29922` | directional/exploratory flags, 3★ |
| Info (blue) | `#58a6ff` | bucket-1 badge, "Next →" handoffs |
| Purple | `#bc8cff` | gold-set "borderline" |

**Radius**: 6px (chips/small), 8–10px (cards), 12px (panels), 20–30px (pills).
**Spacing**: 8-based-ish — common gaps 8/12/16/20/24px; section rhythm 32–48px; main padding `36px 48px 80px`.
**Charts**: bar height 22–28px; histogram height ~150px; confusion cells ~51×38px.

---

## Assets

No image assets. One inline SVG line chart (discovery trend) and one inline SVG confusion-matrix
heatmap — both data-driven, redraw with your charting library. No logos or brand imagery are used
(the "Spotify" wordmark is text only; substitute per your own brand/legal guidance).

---

## Files

- `Review Intelligence Dashboard (visualiser).html` — open this first; it is the full design.
- `dashboard-design-spec.md` — narrative/content rationale (the "why").
- `source/data.js` — the binding data schema (the "what your scraper outputs").
- `source/V5 Atlas.dc.html` — prototype markup + render logic, for pixel reference.
