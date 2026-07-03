# Phase 8 — Dashboard (React + Vite + Recharts)

**Objective:** recreate the prototype design in a real component stack, reading the
committed `window.REVIEW_DATA` snapshot — display only, zero analysis.

**Stack:** React 18 + Vite 5 + Recharts. Static SPA, no backend.

**Structure:**
- `src/review_data.json` — the committed Android snapshot (copied from `data/REVIEW_DATA.android.json`).
- `src/App.jsx` — sidebar nav + section routing (`activeSection` state).
- `src/sections/Overview.jsx` — hero, share-of-voice, rating comparison (effect size + CI),
  rating histogram + discovery trend (**Recharts**), delight, sentiment split.
- `src/sections/Discovery.jsx` — behaviours, the repetition **bridge** (reframed imposed-dominant),
  Bucket 2/3 theme bars, unmet needs + segments.
- `src/sections/Evidence.jsx` — filter chips (data-driven), sub-theme rail, verbatim quote cards.
- `src/sections/Methodology.jsx` — funnel, gold-set headline, limitations, and the inline-expanding
  evaluation layer (7 audit visuals).
- `src/tokens.js` — design tokens from the README (Sora, colour palette, spacing).

**Faithful but data-driven:** the prototype hard-codes some overview numbers
(`17.5%`, `−0.8★`); this port wires every value to the real snapshot. Adapted where our
data differs: the confusion matrix is the **discovery sub-theme** matrix (broad gold parked),
the country/platform chips derive from the actual quotes (Android / GLOBAL), and the bridge
renders the honest ~0-chosen / imposed-dominant split.

**Verified:** `npm run build` succeeds; all four sections render with real data; Recharts
charts emit SVG; nav + evidence filters + eval expander all work (checked in a live preview).

**How to run:**
```
cd phases/phase-8-dashboard
npm install
npm run dev      # http://localhost:4178
npm run build    # -> dist/  (deploy this to Vercel in Phase 9)
```
