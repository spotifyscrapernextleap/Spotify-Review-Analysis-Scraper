import React, { useState } from 'react';
import { C } from '../tokens.js';

// Sentiment comes from the Layer-1 LLM pass (positive|negative|mixed); fall back to
// the star rating only if a quote has no stored sentiment.
const SENT = {
  positive: { label: 'Positive', color: C.green },
  negative: { label: 'Negative', color: C.red },
  mixed: { label: 'Mixed', color: C.amber },
};
const sentOf = (q) => (q.sentiment && SENT[q.sentiment]
  ? q.sentiment
  : (q.rating >= 3 ? 'positive' : 'negative'));

export default function Evidence({ d, track }) {
  const themes = d.discovery.themes.filter((t) => (d.quotes[t.id] || []).length > 0);
  const [selectedTheme, setSelectedTheme] = useState(themes[0]?.id || d.discovery.themes[0].id);
  const [evSentiment, setEvSentiment] = useState('all');
  const [evCountry, setEvCountry] = useState('all');

  // Platform is fixed by the active track toggle, so we don't offer it as a filter.
  // Country IS a real dimension on iOS (US/GB/CA/IN/AU); on Android every quote is GLOBAL.
  const allQuotes = Object.values(d.quotes).flat();
  const countries = [...new Set(allQuotes.map((q) => q.store))].filter(Boolean);
  const showCountry = countries.length > 1;

  const themesById = {};
  d.discovery.themes.forEach((t) => { themesById[t.id] = t; });
  const selName = themesById[selectedTheme]?.name || '';

  const raw = d.quotes[selectedTheme] || [];
  const filtered = raw.filter((q) => {
    if (evSentiment !== 'all' && sentOf(q) !== evSentiment) return false;
    if (evCountry !== 'all' && q.store !== evCountry) return false;
    return true;
  });

  const Chips = ({ label, opts, cur, set }) => (
    <div>
      <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>{label}</div>
      <div style={{ display: 'flex', gap: 6 }}>
        {opts.map((o) => {
          const on = cur === o.val;
          return (
            <div key={o.val} onClick={() => set(o.val)}
              style={{ fontSize: 12, padding: '5px 12px', borderRadius: 6, cursor: 'pointer',
                background: on ? 'rgba(29,185,84,0.12)' : C.bg, color: on ? C.green : C.text2,
                border: `1px solid ${on ? 'rgba(29,185,84,0.3)' : C.border}` }}>{o.label}</div>
          );
        })}
      </div>
    </div>
  );

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: C.muted, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 8 }}>Evidence Explorer</div>
        <div style={{ fontSize: 24, fontWeight: 700, color: C.white, letterSpacing: '-0.02em' }}>The receipts</div>
        <div style={{ fontSize: 13, color: C.text2, marginTop: 6 }}>Pull any thread and check it against raw text. Each quote is the verbatim review that justified its tag.</div>
      </div>

      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginBottom: 24, padding: '16px 20px', background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10 }}>
        <Chips label="Sentiment" cur={evSentiment} set={setEvSentiment}
          opts={[{ label: 'All', val: 'all' }, { label: 'Positive', val: 'positive' }, { label: 'Negative', val: 'negative' }, { label: 'Mixed', val: 'mixed' }]} />
        {showCountry && (
          <Chips label="Country" cur={evCountry} set={setEvCountry}
            opts={[{ label: 'All', val: 'all' }, ...countries.map((c) => ({ label: c, val: c }))]} />
        )}
      </div>

      <div style={{ display: 'flex', gap: 24 }}>
        {/* THEME LIST */}
        <div style={{ width: 220, flexShrink: 0 }}>
          <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 10 }}>Discovery sub-theme</div>
          {d.discovery.themes.map((t) => {
            const on = selectedTheme === t.id;
            const has = (d.quotes[t.id] || []).length;
            return (
              <div key={t.id} onClick={() => setSelectedTheme(t.id)}
                style={{ padding: '9px 14px', cursor: 'pointer', fontSize: 12, color: on ? C.white : C.text2,
                  background: on ? 'rgba(29,185,84,0.1)' : 'transparent', borderRadius: 6, marginBottom: 4,
                  border: `1px solid ${on ? 'rgba(29,185,84,0.25)' : 'transparent'}`, fontWeight: on ? 600 : 400 }}>
                <div>{t.name}</div>
                <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{has} quotes · {t.count} coded</div>
              </div>
            );
          })}
        </div>

        {/* QUOTES */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 14 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: C.white }}>{selName}</div>
            <div style={{ fontSize: 11, color: C.muted }}>{filtered.length} of {raw.length} quotes</div>
          </div>
          {filtered.map((q, i) => {
            const s = sentOf(q);
            const meta = SENT[s];
            const accent = meta.color;
            const others = q.otherThemes || [];
            return (
              <div key={i} style={{ background: C.surface, borderRadius: 8, padding: '18px 20px', marginBottom: 10, border: `1px solid ${C.border}`, borderLeft: `3px solid ${accent}` }}>
                <div style={{ fontSize: 13, color: C.textBright, lineHeight: 1.6, fontStyle: 'italic' }}>"{q.text}"</div>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 12, flexWrap: 'wrap' }}>
                  {others.map((nm, j) => (
                    <div key={j} title="Also tagged under this sub-theme"
                      style={{ fontSize: 10, color: C.text2, background: 'transparent', border: `1px solid ${C.border}`, padding: '3px 8px', borderRadius: 4 }}>also: {nm}</div>
                  ))}
                  <div style={{ fontSize: 11, color: accent, fontWeight: 600 }}>{meta.label}</div>
                  <div style={{ fontSize: 11, color: q.rating <= 2 ? C.red : C.amber }}>{'★'.repeat(q.rating)}{'☆'.repeat(5 - q.rating)}</div>
                  <div style={{ fontSize: 11, color: C.muted }}>{q.platform} · {q.store}</div>
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center', fontSize: 12, color: C.muted, background: C.surface, borderRadius: 8, border: `1px dashed ${C.border}` }}>No quotes match these filters.</div>
          )}
        </div>
      </div>
    </>
  );
}
