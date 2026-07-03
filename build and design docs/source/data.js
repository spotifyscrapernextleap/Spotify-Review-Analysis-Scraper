// Spotify Review Intelligence — Mock Data Snapshot
// Structurally accurate placeholder data for dashboard prototyping.
// Numbers are plausible but fabricated; quotes are illustrative.

window.REVIEW_DATA = {
  funnel: {
    collected: 4832,
    deduplicated: 3891,
    english: 3412,
    tierA: 1847,
    tierB: 892,
    tierC: 673,
    substantive: 2739,
    discoveryAll: 479,
    deepCoded: 412
  },

  window: {
    collection: "Jun 2025 – Jun 2026",
    analysis: "Dec 2025 – Jun 2026",
    appUpdates: 4,
    justification: "6-month window spanning 4 major app updates. Recent enough to reflect the current product; wide enough to reach thematic saturation at ~380 reviews."
  },

  platforms: {
    ios: { count: 1706, avgRating: 3.1 },
    android: { count: 1706, avgRating: 3.3 }
  },

  baseline: {
    totalReviews: 3412,
    avgRating: 3.2,
    distribution: [
      { stars: 1, pct: 28, count: 955 },
      { stars: 2, pct: 18, count: 614 },
      { stars: 3, pct: 15, count: 512 },
      { stars: 4, pct: 17, count: 580 },
      { stars: 5, pct: 22, count: 751 }
    ]
  },

  categories: [
    { id: "playback", name: "Playback / Technical", count: 631, pct: 23.0, avgRating: 1.8, color: "#E5484D" },
    { id: "discovery", name: "Discovery & Recs", count: 479, pct: 17.5, avgRating: 2.4, color: "#1DB954" },
    { id: "ux", name: "UX / Navigation", count: 411, pct: 15.0, avgRating: 2.6, color: "#3E63DD" },
    { id: "pricing", name: "Pricing / Account", count: 370, pct: 13.5, avgRating: 2.1, color: "#F5A623" },
    { id: "catalogue", name: "Catalogue / Availability", count: 288, pct: 10.5, avgRating: 2.9, color: "#8E4EC6" },
    { id: "audio", name: "Audio Quality", count: 192, pct: 7.0, avgRating: 2.3, color: "#12A594" },
    { id: "other", name: "Other / Multiple", count: 368, pct: 13.4, avgRating: 2.5, color: "#6B7280" }
  ],

  discovery: {
    totalMentions: 479,
    deepCoded: 412,
    avgRating: 2.4,
    effectSize: -0.8,
    themes: [
      { id: "repeat", name: "Same songs on repeat", count: 89, pct: 21.6, sentiment: 1.9, group: "repetition" },
      { id: "mismatch", name: "Recs don't match taste", count: 74, pct: 18.0, sentiment: 2.2, group: "relevance" },
      { id: "bubble", name: "Filter bubble / echo chamber", count: 56, pct: 13.6, sentiment: 2.1, group: "repetition" },
      { id: "shuffle", name: "Shuffle isn't random", count: 49, pct: 11.9, sentiment: 1.7, group: "repetition" },
      { id: "stale", name: "Discover Weekly stale", count: 42, pct: 10.2, sentiment: 2.5, group: "features" },
      { id: "context", name: "Algorithm ignores context", count: 37, pct: 9.0, sentiment: 2.3, group: "relevance" },
      { id: "safe", name: "Too safe / no diversity", count: 31, pct: 7.5, sentiment: 2.6, group: "repetition" },
      { id: "good", name: "Good but inconsistent", count: 19, pct: 4.6, sentiment: 3.4, group: "positive" },
      { id: "control", name: "Want tuning controls", count: 15, pct: 3.6, sentiment: 2.8, group: "features" }
    ],
    repetitionCluster: {
      themeIds: ["repeat", "bubble", "shuffle", "safe"],
      totalCount: 225,
      pctOfDiscovery: 54.6
    }
  },

  behaviors: [
    { name: "Background listening (work / study)", mentions: 89 },
    { name: "Active exploration / new artists", mentions: 67 },
    { name: "Workout / gym motivation", mentions: 54 },
    { name: "Mood-based listening", mentions: 42 },
    { name: "Curating personal playlists", mentions: 38 },
    { name: "Commute / driving", mentions: 31 },
    { name: "Social / sharing music", mentions: 22 }
  ],

  unmetNeeds: [
    { need: "Separate 'comfort' and 'explore' modes", mentions: 64, strength: "strong" },
    { need: "Direct algorithm feedback ('less of this, more of that')", mentions: 52, strength: "strong" },
    { need: "True randomness in shuffle", mentions: 48, strength: "strong" },
    { need: "Context-aware recs (time, activity, mood)", mentions: 41, strength: "moderate" },
    { need: "Discover Weekly that evolves with taste", mentions: 35, strength: "moderate" },
    { need: "Genre / mood exploration beyond playlists", mentions: 28, strength: "emerging" }
  ],

  segments: [
    { name: "Passive Listeners", size: 34, topTheme: "Same songs on repeat", avgRating: 2.8, discoveryPct: 15 },
    { name: "Active Explorers", size: 28, topTheme: "Filter bubble", avgRating: 2.1, discoveryPct: 31 },
    { name: "Playlist Curators", size: 22, topTheme: "Recs don't match taste", avgRating: 2.5, discoveryPct: 24 },
    { name: "Context Switchers", size: 16, topTheme: "Algorithm ignores context", avgRating: 2.6, discoveryPct: 22 }
  ],

  validation: {
    goldSetSize: 50,
    overallAccuracy: 84,
    categoryAccuracy: 88,
    themeAccuracy: 79,
    kappa: 0.72
  },

  trends: [
    { month: "Dec", reviews: 312, discoveryPct: 16.2 },
    { month: "Jan", reviews: 445, discoveryPct: 18.1 },
    { month: "Feb", reviews: 389, discoveryPct: 17.8 },
    { month: "Mar", reviews: 502, discoveryPct: 19.3 },
    { month: "Apr", reviews: 421, discoveryPct: 16.7 },
    { month: "May", reviews: 398, discoveryPct: 17.2 },
    { month: "Jun", reviews: 272, discoveryPct: 15.9 }
  ],

  quotes: {
    repeat: [
      { text: "I keep hearing the same 20 songs no matter what playlist I open. It's like Spotify forgot other music exists.", rating: 1, platform: "iOS", store: "US" },
      { text: "Daily Mix is just yesterday's Daily Mix. Same recommendations cycling for months now.", rating: 2, platform: "Android", store: "UK" },
      { text: "My Release Radar keeps showing songs I listened to 6 months ago. Not exactly 'new releases'.", rating: 2, platform: "iOS", store: "CA" },
      { text: "Every single playlist — Discover Weekly, Daily Mix, Radio — all the same pool of 50 songs.", rating: 1, platform: "Android", store: "US" }
    ],
    mismatch: [
      { text: "I listen exclusively to jazz and classical. Spotify keeps pushing pop and hip-hop. Makes zero sense.", rating: 1, platform: "Android", store: "US" },
      { text: "Listened to one K-pop song for a friend. Now my entire home page is K-pop. One song.", rating: 2, platform: "iOS", store: "UK" },
      { text: "The algorithm clearly doesn't understand the difference between genres I explore casually and what I actually like.", rating: 2, platform: "iOS", store: "AU" }
    ],
    bubble: [
      { text: "Feel trapped in a recommendation bubble. The more I listen, the narrower everything gets.", rating: 2, platform: "Android", store: "US" },
      { text: "Spotify used to introduce me to new genres. Now it just feeds me slight variations of what I already know.", rating: 2, platform: "iOS", store: "CA" },
      { text: "I've been on this app for 5 years and my Discover Weekly has gotten worse every year. It's an echo chamber.", rating: 2, platform: "Android", store: "UK" }
    ],
    shuffle: [
      { text: "Shuffle plays the same 5 songs out of a 200-song playlist. Every. Single. Time.", rating: 1, platform: "iOS", store: "US" },
      { text: "Hit shuffle on 500 songs and somehow hear the same ones within the first 10. This is not random.", rating: 1, platform: "Android", store: "AU" },
      { text: "I've tested it. Shuffle clearly favors certain tracks. Probably whatever Spotify gets paid more for.", rating: 1, platform: "iOS", store: "US" }
    ],
    stale: [
      { text: "Discover Weekly used to be my favorite feature. Now it's the same artists reshuffled every week.", rating: 3, platform: "iOS", store: "US" },
      { text: "DW hasn't surprised me in months. It's like the algorithm gave up trying.", rating: 2, platform: "Android", store: "UK" }
    ],
    context: [
      { text: "I listen to focus music while working and metal while lifting. Spotify mixes them into one confused profile.", rating: 2, platform: "Android", store: "US" },
      { text: "Why can't it understand that my 3am ambient listening is different from my Saturday party playlist?", rating: 2, platform: "iOS", store: "UK" }
    ],
    safe: [
      { text: "Recommendations are so safe and predictable. I want to be challenged, not coddled.", rating: 3, platform: "iOS", store: "US" },
      { text: "It only recommends music that sounds exactly like what I already listen to. Where's the adventure?", rating: 2, platform: "Android", store: "CA" }
    ],
    good: [
      { text: "When it works, the recommendations are amazing. But it's so inconsistent — great one week, terrible the next.", rating: 3, platform: "iOS", store: "US" },
      { text: "Found some incredible artists through Daily Mix. Wish it could maintain that quality consistently.", rating: 4, platform: "Android", store: "UK" }
    ],
    control: [
      { text: "I wish I could tell the algorithm 'less of this, more of that' instead of just thumbs up/down.", rating: 3, platform: "iOS", store: "US" },
      { text: "Give us sliders for how adventurous we want recs to be. Let us control our own discovery.", rating: 3, platform: "Android", store: "US" }
    ]
  },

  crosswalk: [
    { q: "Q1", question: "Why do users struggle to discover new music?", sections: "Discovery Sub-themes · Share of Voice", confidence: "Strong", summary: "Repetition dominates at 54.6% of discovery complaints. The algorithm creates filter bubbles, shuffle feels non-random, and recs calcify around existing taste." },
    { q: "Q2", question: "Most common frustrations with recommendations?", sections: "Discovery Sub-themes (ranked) · Evidence Quotes", confidence: "Strong", summary: "Same songs on repeat (21.6%), taste mismatch (18.0%), filter bubble (13.6%), and non-random shuffle (11.9%) are the top four." },
    { q: "Q3", question: "What listening behaviours are users trying to achieve?", sections: "User Behaviours Panel", confidence: "Directional", summary: "Background work/study listening (89), active exploration (67), and workout motivation (54) are the most disclosed contexts." },
    { q: "Q4", question: "What causes repeated listening to the same content?", sections: "Repetition Theme Group", confidence: "Strong", summary: "Algorithmic reinforcement, non-random shuffle, and recommendation safety combine to keep users in a loop they didn't choose." },
    { q: "Q5", question: "Which segments experience different discovery challenges?", sections: "Segment Breakdown", confidence: "Exploratory", summary: "Active Explorers are most frustrated (2.1 avg) and most vocal about discovery (31%). Passive Listeners complain less but specifically about repetition." },
    { q: "Q6", question: "What unmet needs emerge consistently?", sections: "Unmet Needs Ranking", confidence: "Strong", summary: "Comfort/explore mode split (64 mentions), direct algorithm feedback (52), and true shuffle randomness (48) are the top three." }
  ],

  limitations: [
    "Reviewers ≠ all users — people who write reviews skew toward strong opinions.",
    "Chronic dissatisfaction (discovery fatigue) is structurally undercounted in reviews.",
    "Segment coverage is partial — only reviews disclosing usage context contribute.",
    "English-only analysis; non-English markets may differ.",
    "6-month analysis window; patterns outside this window are not captured.",
    "Automated categorisation accuracy is 84% — ~1 in 6 may be miscategorised."
  ],

  // ---- Effect size with confidence interval (Section 1A) ----
  effect: {
    gap: -0.8,
    ciLow: -1.0,
    ciHigh: -0.6,
    note: "The interval excludes zero, so the gap is unlikely to be noise."
  },

  // ---- Discovery share of voice over time (Section 1A) ----
  // (line read off the existing `trends` array; direction summarised here)
  trendDirection: {
    summary: "Broadly flat across the window — discovery mention rate oscillates 16–19% with no sustained trend.",
    label: "Flat"
  },

  // ---- 1B. Delight (the counterweight, kept deliberately light) ----
  delight: {
    positiveShare: 31,
    positiveCount: 849,
    byCategory: [
      { name: "Catalogue / Availability", pct: 58 },
      { name: "Audio Quality", pct: 44 },
      { name: "Discovery & Recs", pct: 22 },
      { name: "UX / Navigation", pct: 19 },
      { name: "Playback / Technical", pct: 14 },
      { name: "Pricing / Account", pct: 11 }
    ],
    topThemes: [
      { name: "Catalogue is huge — always has the song", count: 142 },
      { name: "Daily Mix occasionally nails it", count: 98 },
      { name: "Audio quality on premium is excellent", count: 76 },
      { name: "Cross-device playback just works", count: 61 }
    ]
  },

  // ---- 1C. Discovery sentiment, in context (pos vs neg share per category) ----
  sentimentSplit: [
    { id: "discovery", name: "Discovery & Recs", pos: 22, neg: 78 },
    { id: "playback", name: "Playback / Technical", pos: 14, neg: 86 },
    { id: "ux", name: "UX / Navigation", pos: 19, neg: 81 },
    { id: "pricing", name: "Pricing / Account", pos: 11, neg: 89 },
    { id: "catalogue", name: "Catalogue / Availability", pos: 58, neg: 42 },
    { id: "audio", name: "Audio Quality", pos: 44, neg: 56 }
  ],
  positiveDiscoveryThemes: [
    { name: "Daily Mix occasionally surprises", count: 41 },
    { name: "Found a new favourite artist", count: 28 },
    { name: "Release Radar caught a drop", count: 17 }
  ],

  // ---- Section 2: bucket assignment for the 3-bucket narrative ----
  // bucket2 = problems FINDING new music; bucket3 = problems with WHAT GETS SERVED
  buckets: {
    finding: { ids: ["stale", "safe", "bubble", "control"], emerging: 12 },
    recs:    { ids: ["mismatch", "repeat", "shuffle", "context"], emerging: 9 }
  },

  // ---- The repetition bridge (chosen vs imposed) ----
  bridge: {
    total: 225,
    chosen: {
      total: 83,
      label: "CHOSEN repetition",
      sub: "A need, not a fault",
      flowsTo: "Flows into unmet needs",
      items: [
        { name: "Comfort listening", count: 38 },
        { name: "Mood / habit", count: 27 },
        { name: "Intentional replay", count: 18 }
      ]
    },
    imposed: {
      total: 142,
      label: "IMPOSED repetition",
      sub: "A discovery / rec failure",
      flowsTo: "Flows into Buckets 2 & 3",
      items: [
        { name: "Filter bubble", count: 56 },
        { name: "Shuffle that isn't random", count: 49 },
        { name: "Recommendations too safe", count: 37 }
      ]
    }
  },

  // ---- Section 4B. Evaluation layer (7 visuals) ----
  evaluation: {
    // 1. Sampling fairness — collected vs store-reported star distribution
    sampling: {
      bars: [
        { stars: 1, collected: 28, store: 21 },
        { stars: 2, collected: 18, store: 12 },
        { stars: 3, collected: 15, store: 11 },
        { stars: 4, collected: 17, store: 18 },
        { stars: 5, collected: 22, store: 38 }
      ],
      note: "Collected reviews skew 16pts more negative at 5★ than each store's publicly reported distribution — consistent with the known reviewer-selection bias. The analysis corrects for this by reading effect sizes within the same pool rather than absolute sentiment."
    },
    // 2. Funnel reconciliation — in = out + removed at every step
    funnelReconcile: [
      { step: "Collected", inN: null, removed: null, reason: "raw pull", outN: 4832 },
      { step: "Deduplicated", inN: 4832, removed: 941, reason: "exact + near-duplicate", outN: 3891 },
      { step: "English only", inN: 3891, removed: 479, reason: "non-English", outN: 3412 },
      { step: "Substantive", inN: 3412, removed: 673, reason: "contentless (Tier C)", outN: 2739 },
      { step: "Discovery mentions", inN: 2739, removed: 2260, reason: "non-discovery", outN: 479 },
      { step: "Deep-coded", inN: 479, removed: 67, reason: "too thin to code", outN: 412 }
    ],
    // 3. Field integrity
    fieldIntegrity: [
      { field: "Rating", valid: 99.4, quarantined: 21 },
      { field: "Review text", valid: 100.0, quarantined: 0 },
      { field: "Date", valid: 98.1, quarantined: 74 },
      { field: "Platform", valid: 99.9, quarantined: 3 },
      { field: "Country", valid: 97.2, quarantined: 108 }
    ],
    // 4. Language-filter spot-check
    languageCheck: {
      falseDrop: 1.8,
      falseKeep: 2.3,
      example: "Bro the recs are so mid, same gaane baar baar — pls fix the algorithm yaar",
      exampleVerdict: "Code-switched Hinglish — correctly KEPT as English-substantive (Latin script, English-parseable intent)."
    },
    // 5. Per-category accuracy — confusion matrix (rows = gold truth, cols = predicted)
    confusion: {
      labels: ["Playback", "Discovery", "UX", "Pricing", "Catalogue", "Audio"],
      matrix: [
        [91, 2, 3, 1, 1, 2],
        [3, 86, 5, 1, 3, 2],
        [4, 6, 84, 3, 2, 1],
        [1, 1, 4, 92, 1, 1],
        [2, 4, 2, 1, 88, 3],
        [3, 2, 1, 1, 4, 89]
      ],
      discoveryAccuracy: 86
    },
    // 6. Gold-set composition
    goldComposition: {
      total: 50,
      borderline: 32,
      easy: 18,
      coverage: [
        { cat: "Discovery", count: 11 },
        { cat: "Playback", count: 9 },
        { cat: "UX", count: 8 },
        { cat: "Catalogue", count: 8 },
        { cat: "Pricing", count: 7 },
        { cat: "Audio", count: 7 }
      ]
    },
    // 7. Abstention calibration
    abstention: {
      confidentShare: 82,
      confidentAccuracy: 89,
      abstainedShare: 18,
      abstainedAccuracy: 61
    }
  }
};
