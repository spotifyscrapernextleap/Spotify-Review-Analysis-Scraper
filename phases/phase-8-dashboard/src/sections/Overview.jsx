import React from 'react';
import { C, fmt } from '../tokens.js';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, BarChart, Bar, Cell, Legend, Tooltip } from 'recharts';

const H2 = ({ children }) => (
  <div style={{ fontSize: 14, fontWeight: 600, color: C.white, marginBottom: 4 }}>{children}</div>
);

export default function Overview({ d, track }) {
  const isIos = track === 'ios';
  const maxCat = Math.max(...d.categories.map((c) => c.sampleCount));
  const maxDist = Math.max(...d.baseline.distribution.map((x) => x.pct));
  const histColor = (s) => (s <= 2 ? C.red : s === 3 ? C.amber : C.green);

  // data-driven share-of-voice caption (works for both tracks)
  const topCat = d.categories[0];
  const discCat = d.categories.find((c) => c.id === 'discovery');

  const funnel = isIos
    ? [
        { v: d.funnel.collected, label: 'Reviews collected', sub: 'Apple App Store · US, GB, CA, IN, AU · mostrecent' },
        { v: d.funnel.english, label: 'Unique English reviews', sub: 'After removing duplicates and non-English text' },
        { v: d.funnel.substantiveCensus, label: 'Substantive reviews', sub: 'Real opinions, classified in full (census, no sampling)' },
        { v: d.discovery.deepCoded, label: 'Deep-coded discovery', sub: 'Confirmed discovery, theme-coded (v3)' },
      ]
    : [
        { v: d.funnel.collected, label: 'Reviews collected', sub: 'Raw Google Play pull across US, GB, IN' },
        { v: d.funnel.english, label: 'Unique English reviews', sub: 'After removing duplicates and non-English text' },
        { v: d.funnel.substantiveCensus, label: 'Substantive reviews', sub: 'Real opinions, after dropping contentless one-liners' },
        { v: d.funnel.sampled, label: 'Classified sample', sub: 'Month-stratified slice, labeled by the LLM' },
      ];

  const maxCountry = isIos ? Math.max(...d.countries.map((c) => c.collected)) : 0;

  return (
    <>
      {/* HEADER */}
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{ fontSize: 28, fontWeight: 700, color: C.white, letterSpacing: '-0.02em' }}>Spotify Review Intelligence Dashboard</div>
        <div style={{ fontSize: 14, color: C.text2, marginTop: 8 }}>An automated system to understand what users are saying about Spotify, and why.</div>
      </div>

      {/* FUNNEL CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1, background: C.border, borderRadius: 12, overflow: 'hidden', marginBottom: 20 }}>
        {funnel.map((h, i) => (
          <div key={i} style={{ background: C.surface, padding: 24, textAlign: 'center' }}>
            <div style={{ fontSize: 34, fontWeight: 700, color: isIos && i === 3 ? C.green : C.white, letterSpacing: '-0.04em' }}>{fmt(h.v)}</div>
            <div style={{ fontSize: 12, color: C.text2, marginTop: 6 }}>{h.label}</div>
            <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{h.sub}</div>
          </div>
        ))}
      </div>

      {/* INTRO */}
      <div style={{ fontSize: 13, color: C.text2, lineHeight: 1.7, marginBottom: 40, maxWidth: 860 }}>
        {isIos
          ? <>This dashboard reads public Spotify reviews from the Apple App Store and classifies them automatically to answer one question: how big is the music-discovery problem relative to everything else, and what exactly are users frustrated about? iOS is a current snapshot ({d.window.analysis.replace('Current snapshot ', '').replace(/[()]/g, '')}), a full census of the reviews the store exposes, so every number is exact.</>
          : <>This dashboard reads public Spotify reviews from the Google Play store and classifies them automatically to answer one question: how big is the music-discovery problem relative to everything else, and what exactly are users frustrated about? Every number below traces back to the real pipeline above, from the full collection down to the classified sample.</>}
      </div>

      {/* ROW: iOS -> per-country (full width) | Android -> distribution + trend */}
      {isIos ? (
        <div style={{ marginBottom: 40 }}>
          <H2>Reviews collected by country</H2>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
            The iTunes RSS feed caps at ~500 mostrecent reviews per storefront. Grey is raw collected, green is what entered analysis after filtering. Unlike Android, iOS country is a genuine dimension.
          </div>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={d.countries} margin={{ top: 18, right: 8, bottom: 0, left: 4 }} barGap={4}>
                <XAxis dataKey="code" tick={{ fill: C.text2, fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis hide domain={[0, maxCountry * 1.15]} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.03)' }} contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11, color: C.text2 }} />
                <Bar dataKey="collected" name="Collected (raw)" fill={C.borderSubtle} radius={[3, 3, 0, 0]} label={{ position: 'top', fill: C.muted, fontSize: 10 }} />
                <Bar dataKey="substantive" name="Substantive" fill={C.green} radius={[3, 3, 0, 0]} label={{ position: 'top', fill: C.text2, fontSize: 10 }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 40 }}>
          <div>
            <H2>Rating distribution</H2>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>Baseline, all {fmt(d.baseline.totalReviews)} rated reviews, including contentless.</div>
            <div style={{ height: 170 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={d.baseline.distribution} margin={{ top: 18, right: 4, bottom: 0, left: 4 }}>
                  <XAxis dataKey="stars" tickFormatter={(s) => `${s}★`} tick={{ fill: C.text2, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis hide domain={[0, maxDist * 1.1]} />
                  <Bar dataKey="pct" radius={[4, 4, 0, 0]} isAnimationActive label={{ position: 'top', fill: C.text2, fontSize: 11, formatter: (v) => `${v}%` }}>
                    {d.baseline.distribution.map((b) => <Cell key={b.stars} fill={histColor(b.stars)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div>
            <H2>Discovery share of voice over time</H2>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
              Direction: <span style={{ color: C.amber, fontWeight: 600 }}>{d.trendDirection.label}</span>. {d.trendDirection.summary}
            </div>
            <div style={{ height: 170 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={d.trends} margin={{ top: 10, right: 8, bottom: 0, left: 8 }}>
                  <defs>
                    <linearGradient id="discFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={C.green} stopOpacity={0.18} />
                      <stop offset="100%" stopColor={C.green} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" tick={{ fill: C.muted, fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis hide domain={[0, Math.max(...d.trends.map((t) => t.discoveryPct)) * 1.4]} />
                  <Area type="monotone" dataKey="discoveryPct" stroke={C.green} strokeWidth={2.5} fill="url(#discFill)" dot={{ r: 3, fill: C.bg, stroke: C.green, strokeWidth: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* SHARE OF VOICE */}
      <div style={{ marginBottom: 40 }}>
        <H2>Share of voice by category</H2>
        <div style={{ fontSize: 13, color: C.text2, lineHeight: 1.7, marginBottom: 8, maxWidth: 860 }}>
          Pricing, ads, and account issues dominate what users complain about ({topCat.pct}%). Discovery and recommendations are a clear second ({discCat?.pct}%), well ahead of everything else.
        </div>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 16 }}>
          Share of the {fmt(d.funnel.contentBearing)} content-bearing {isIos ? 'reviews (full census)' : 'sample reviews'} that raise each category. A review can raise more than one, so shares total over 100%. Each bar shows its raw count.
        </div>
        {d.categories.map((c) => {
          const isD = c.id === 'discovery';
          return (
            <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '7px 0' }}>
              <div style={{ width: 180, fontSize: 13, color: isD ? C.green : C.text, fontWeight: isD ? 600 : 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.name}</div>
              <div style={{ flex: 1, height: 26, background: C.surface, borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: 6, width: `${(c.sampleCount / maxCat) * 100}%`, background: isD ? C.green : C.borderSubtle, transition: 'width 0.5s' }} />
              </div>
              <div style={{ width: 120, textAlign: 'right', fontSize: 12, fontWeight: 600, color: isD ? C.green : C.text }}>{c.pct}% (n={fmt(c.sampleCount)})</div>
              <div style={{ width: 36, textAlign: 'right', fontSize: 11, color: C.muted }}>{c.avgRating}★</div>
            </div>
          );
        })}
      </div>

      {/* RATING COMPARISON (effect-gap value removed per spec; bars retained) */}
      <div style={{ marginBottom: 40 }}>
        <H2>Rating comparison</H2>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>Average stars: all reviews vs the discovery reviews.</div>
        <div style={{ background: C.surface, borderRadius: 10, padding: 24, border: `1px solid ${C.border}`, marginTop: 8 }}>
          {[
            { label: `All reviews (n=${fmt(d.baseline.totalReviews)})`, val: d.baseline.avgRating, color: C.text, bar: C.muted },
            { label: `Discovery reviews (n=${fmt(d.discovery.sampleN)})`, val: d.discovery.avgRating, color: C.green, bar: C.green },
          ].map((r) => (
            <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
              <div style={{ width: 220, fontSize: 12, color: C.text2 }}>{r.label}</div>
              <div style={{ flex: 1, height: 26, background: C.border, borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: r.bar, borderRadius: 4, width: `${(r.val / 5) * 100}%` }} />
              </div>
              <div style={{ fontSize: 17, fontWeight: 700, color: r.color, width: 56, textAlign: 'right' }}>{r.val}★</div>
            </div>
          ))}
        </div>
      </div>

      {/* CATEGORY SENTIMENT */}
      <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 32 }}>
        <H2>Category Sentiment</H2>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 18 }}>A representation of the ratio of positive and negative reviews within each category. All categories appear, so the engine classifies everything, not just discovery.</div>
        {d.sentimentSplit.map((s) => {
          const isD = s.id === 'discovery';
          return (
            <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 0' }}>
              <div style={{ width: 180, fontSize: 13, color: isD ? C.green : C.text, fontWeight: isD ? 600 : 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</div>
              <div style={{ flex: 1, height: 24, borderRadius: 6, overflow: 'hidden', display: 'flex' }}>
                <div style={{ height: '100%', width: `${s.pos}%`, background: C.green, opacity: 0.85, display: 'flex', alignItems: 'center', paddingLeft: 8, fontSize: 10, color: '#04130a', fontWeight: 600 }}>{s.pos}%</div>
                <div style={{ height: '100%', width: `${s.neg}%`, background: C.red, opacity: 0.8, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: 8, fontSize: 10, color: '#1a0303', fontWeight: 600 }}>{s.neg}%</div>
              </div>
            </div>
          );
        })}
        <div style={{ marginTop: 18, background: C.surface, borderRadius: 8, padding: '16px 20px', border: `1px solid ${C.border}` }}>
          <div style={{ fontSize: 12, color: C.text2, marginBottom: 10 }}>Common aspects inside the <span style={{ color: C.green }}>positive</span> discovery reviews</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {d.positiveDiscoveryThemes.map((pt) => (
              <div key={pt.name} style={{ fontSize: 12, color: C.text, background: 'rgba(29,185,84,0.08)', border: '1px solid rgba(29,185,84,0.2)', padding: '6px 12px', borderRadius: 20 }}>{pt.name} <span style={{ color: C.green, fontWeight: 600 }}>· {pt.count}</span></div>
            ))}
          </div>
        </div>
        <div style={{ marginTop: 24, padding: '16px 20px', background: 'rgba(88,166,255,0.05)', border: '1px solid rgba(88,166,255,0.15)', borderRadius: 8, fontSize: 12, color: C.text2, lineHeight: 1.6 }}>
          <span style={{ color: C.blue, fontWeight: 600 }}>Next →</span> The overview proves discovery is real, sized, and not universally hated. The natural next question is <span style={{ color: C.text }}>why</span>. For frustrated users, what is going wrong, and what were they trying to do?
        </div>
      </div>
    </>
  );
}
