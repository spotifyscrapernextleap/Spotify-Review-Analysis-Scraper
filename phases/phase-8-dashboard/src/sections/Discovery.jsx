import React from 'react';
import { C, fmt } from '../tokens.js';

// Editorial summaries per sub-theme (verified copy). Counts/percentages come from data.
const SUMMARY = {
  control: 'The single biggest discovery complaint. Users say the app overrides their choices: it adds songs to their playlists, plays tracks they did not pick, and will not let them simply choose what to hear. The grievance is loss of control, not bad taste.',
  freegate: 'Free-tier limits gate discovery itself. Shuffle-only playback, capped skips, and repeat restrictions stop users from choosing or exploring music, under constant prompts to buy Premium.',
  dj: 'The AI DJ underdelivers: it ignores taste, repeats picks, cuts songs short, or carries bugs. Often raised alongside praise for the feature’s potential.',
  newmusic: 'A smaller, distinct ask: users struggle to find genuinely new music, wanting fresh and trending tracks rather than the same familiar rotation.',
  mismatch: 'Recommendations miss the mark. Users report the wrong genre or mood, an algorithm leaning on old history instead of what they are playing now, and tracks unrelated to their taste.',
  smartrec: 'The constructive counterpart. Rather than only complaining, these users ask for better tools: smarter personalization, custom mixes, and direct feedback levers. The one sub-theme that tends to skew positive.',
  pushy: 'Users feel content is forced on them, most often AI-generated music and promoted artists pushed into their listening despite repeated skips and “do not recommend” signals.',
};

const SectionHead = ({ n, title, sub }) => (
  <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 18 }}>
    <div style={{ fontSize: 30, fontWeight: 800, color: C.borderSubtle, letterSpacing: '-0.04em', lineHeight: 1, flexShrink: 0 }}>{n}</div>
    <div>
      <div style={{ fontSize: 18, fontWeight: 700, color: C.white, letterSpacing: '-0.01em' }}>{title}</div>
      <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>{sub}</div>
    </div>
  </div>
);

export default function Discovery({ d, track }) {
  const isIos = track === 'ios';
  const themesById = {};
  d.discovery.themes.forEach((t) => { themesById[t.id] = t; });

  const funnel = [
    { v: d.funnel.sampled, label: isIos ? 'Classified census' : 'Stratified sample', sub: isIos ? 'All substantive candidates, no sampling' : 'Classified by the broad LLM pass' },
    { v: d.funnel.contentBearing, label: 'Content-bearing', sub: 'After dropping contentless reviews' },
    { v: isIos ? d.funnel.discoveryAll : d.discovery.sampleN, label: 'Discovery-flagged', sub: isIos ? 'Raised discovery, incl. recovered from ux/updates' : 'Raised discovery or recommendations' },
    { v: d.discovery.deepCoded, label: 'Deep-coded discovery', sub: 'Confirmed and theme-coded (v3 strict gate)' },
  ];

  // section 02: all problem sub-themes (love is the counterweight, shown separately)
  const barThemes = d.discovery.themes.filter((t) => t.group !== 'positive').slice().sort((a, b) => b.count - a.count);
  const maxBar = Math.max(...barThemes.map((t) => t.count));
  const isRep = (t) => t.group === 'repetition';

  const BucketCards = ({ ids }) => {
    const items = ids.map((id) => themesById[id]).filter(Boolean).sort((a, b) => b.count - a.count);
    return (
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${items.length}, 1fr)`, gap: 1, background: C.border, borderRadius: 10, overflow: 'hidden' }}>
        {items.map((t) => {
          const pos = t.sentiment >= 3;
          return (
            <div key={t.id} style={{ background: C.surface, padding: '20px 20px 22px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: C.white, marginBottom: 12, minHeight: 34 }}>{t.name}</div>
              <div style={{ fontSize: 26, fontWeight: 700, color: pos ? C.green : C.red, letterSpacing: '-0.03em' }}>{t.pct}%</div>
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 9, fontWeight: 600, color: C.muted, letterSpacing: 0.5, textTransform: 'uppercase', marginBottom: 6 }}>Summary</div>
                <div style={{ fontSize: 12, color: C.text2, lineHeight: 1.6 }}>{SUMMARY[t.id]}</div>
                <div style={{ fontSize: 10, color: C.muted, fontStyle: 'italic', marginTop: 12 }}>synthesised from {fmt(t.count)} reviews</div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const br = d.bridge;
  const BridgeCard = ({ data, color, faint }) => (
    <div style={{ background: `${color}0d`, border: `1px solid ${color}33`, borderRadius: 10, padding: 20 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4 }}>
        <div style={{ fontSize: 26, fontWeight: 700, color, letterSpacing: '-0.03em' }}>{data.total}</div>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{data.label}</div>
      </div>
      <div style={{ fontSize: 11, color, marginBottom: 14 }}>{data.sub}</div>
      {faint && <div style={{ fontSize: 11, color: C.muted, fontStyle: 'italic', padding: '4px 0 10px' }}>{faint}</div>}
      {data.items.map((it) => (
        <div key={it.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderTop: `1px solid ${color}1a`, fontSize: 12 }}>
          <div style={{ color: C.text2 }}>{it.name}</div>
          <div style={{ color: C.text, fontWeight: 600 }}>n={fmt(it.count)}</div>
        </div>
      ))}
      <div style={{ fontSize: 11, color: C.muted, marginTop: 12, fontStyle: 'italic' }}>{'↓'} {data.flowsTo}</div>
    </div>
  );

  return (
    <>
      {/* HEADER */}
      <div style={{ textAlign: 'center', marginBottom: 36 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: C.muted, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 10 }}>Discovery Deep Dive</div>
        <div style={{ fontSize: 26, fontWeight: 700, color: C.white, letterSpacing: '-0.02em' }}>What's going wrong, and what users were trying to do</div>
        <div style={{ fontSize: 13, color: C.text2, marginTop: 10, maxWidth: 640, marginLeft: 'auto', marginRight: 'auto', lineHeight: 1.6 }}>
          {fmt(d.discovery.deepCoded)} deep-coded discovery reviews, drawn from a {isIos ? `full census of ${fmt(d.funnel.substantiveCensus)} substantive reviews` : `stratified sample of ${fmt(d.funnel.sampled)}`}. The data points to the answers, it never announces them.
        </div>
      </div>

      {/* 01 FUNNEL */}
      <div style={{ marginBottom: 44 }}>
        <SectionHead n="01" title="The funnel" sub={isIos ? `From a ${fmt(d.funnel.substantiveCensus)}-review census down to ${fmt(d.discovery.deepCoded)} deep-coded discovery reviews` : `From a ${fmt(d.funnel.sampled)}-review stratified sample down to ${fmt(d.discovery.deepCoded)} deep-coded discovery reviews`} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1, background: C.border, borderRadius: 12, overflow: 'hidden' }}>
          {funnel.map((h, i) => (
            <div key={i} style={{ background: C.surface, padding: 22, textAlign: 'center' }}>
              <div style={{ fontSize: 30, fontWeight: 700, color: i === 3 ? C.green : C.white, letterSpacing: '-0.04em' }}>{fmt(h.v)}</div>
              <div style={{ fontSize: 12, color: C.text2, marginTop: 6 }}>{h.label}</div>
              <div style={{ fontSize: 10, color: C.muted, marginTop: 3, lineHeight: 1.4 }}>{h.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 02 SUB-THEMES */}
      <div style={{ marginBottom: 44 }}>
        <SectionHead n="02" title="The sub-themes" sub="Share of the deep-coded discovery reviews raising each sub-theme. The repetition cluster (repeat and shuffle) is highlighted. Reviews can raise more than one, so shares total over 100%." />
        {barThemes.map((t) => (
          <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 0' }}>
            <div style={{ width: 210, fontSize: 13, color: isRep(t) ? C.green : C.text, fontWeight: isRep(t) ? 600 : 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.name}</div>
            <div style={{ flex: 1, height: 24, background: C.surface, borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ height: '100%', borderRadius: 4, width: `${(t.count / maxBar) * 100}%`, background: isRep(t) ? C.green : C.borderSubtle, transition: 'width 0.5s' }} />
            </div>
            <div style={{ width: 48, textAlign: 'right', fontSize: 13, fontWeight: 600, color: isRep(t) ? C.green : C.text }}>{t.pct}%</div>
            <div style={{ width: 44, textAlign: 'right', fontSize: 11, color: C.muted }}>n={fmt(t.count)}</div>
          </div>
        ))}
      </div>

      {/* 03 FINDING */}
      <div style={{ marginBottom: 44 }}>
        <SectionHead n="03" title="Problems finding new music" sub="Sub-themes of finding and controlling what plays. Addresses Q1." />
        <BucketCards ids={d.buckets.finding.ids} />
        <div style={{ fontSize: 11, color: C.muted, marginTop: 10, fontStyle: 'italic' }}>+ emerging / other: {d.buckets.finding.emerging} reviews. Every deep-coded review fit a theme, nothing force-fit.</div>
      </div>

      {/* 04 RECS */}
      <div style={{ marginBottom: 44 }}>
        <SectionHead n="04" title="Problems with the recommendation system" sub="Sub-themes of what gets served. Addresses Q2." />
        <BucketCards ids={d.buckets.recs.ids} />
        <div style={{ fontSize: 11, color: C.muted, marginTop: 10, fontStyle: 'italic' }}>+ emerging / other: {d.buckets.recs.emerging} reviews.</div>
      </div>

      {/* 05 NEEDS + SEGMENT NOTE */}
      <div style={{ marginBottom: 44 }}>
        <SectionHead n="05" title="Inferential reads, needs and segments" sub="Inferred from patterns across the whole pool. Directional synthesis, not slices of the sub-themes above." />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>Recurring unmet needs</div>
            <div style={{ fontSize: 10, color: C.muted, marginBottom: 14 }}>Ranked by frequency. Addresses Q6.</div>
            {d.unmetNeeds.map((n, i) => {
              const sc = n.strength === 'strong' ? C.green : n.strength === 'moderate' ? C.amber : C.muted;
              return (
                <div key={n.need} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '11px 16px', background: C.surface, borderRadius: 8, marginBottom: 6, border: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: C.borderSubtle, width: 24, textAlign: 'center' }}>{i + 1}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, color: C.textBright, fontWeight: 500 }}>{n.need}</div>
                    <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>{fmt(n.mentions)} mentions</div>
                  </div>
                  <div style={{ fontSize: 9, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.4, color: sc, padding: '3px 9px', borderRadius: 4, border: `1px solid ${sc}55` }}>{n.strength}</div>
                </div>
              );
            })}
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>Use-case segments</div>
            <div style={{ fontSize: 10, color: C.muted, marginBottom: 14 }}>Addresses Q5.</div>
            <div style={{ padding: '18px 20px', background: C.surface, borderRadius: 8, border: `1px dashed ${C.border}`, fontSize: 12, color: C.text2, lineHeight: 1.7 }}>
              Reviews rarely disclose a listening context (commute, workout, focus, sleep), so use-case segmentation is not reliable in this data. Very few reviews name a context, far too few to size segments. The signal that does appear is directional only, so we leave it out rather than overstate it.
            </div>
          </div>
        </div>
      </div>

      {/* 06 COUNTERWEIGHT */}
      <div style={{ marginBottom: 44 }}>
        <SectionHead n="06" title="The counterweight" sub="What users love. Deliberately shallow, a counterweight not a second investigation." />
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 24 }}>
          <div>
            <div style={{ fontSize: 12, color: C.text2, marginBottom: 12 }}>Positive-sentiment share by category</div>
            {d.delight.byCategory.map((dc) => (
              <div key={dc.name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '5px 0' }}>
                <div style={{ width: 150, fontSize: 12, color: C.text2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{dc.name}</div>
                <div style={{ flex: 1, height: 18, background: C.surface, borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ height: '100%', borderRadius: 4, width: `${dc.pct}%`, background: C.green, opacity: 0.7 }} />
                </div>
                <div style={{ width: 36, textAlign: 'right', fontSize: 12, fontWeight: 600, color: C.text }}>{dc.pct}%</div>
              </div>
            ))}
          </div>
          <div>
            <div style={{ fontSize: 12, color: C.text2, marginBottom: 12 }}>Top delight themes</div>
            {d.delight.topThemes.map((t) => (
              <div key={t.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: C.surface, borderRadius: 8, marginBottom: 6, border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 12, color: C.text }}>{t.name}</div>
                <div style={{ fontSize: 12, fontWeight: 600, color: C.green, flexShrink: 0, marginLeft: 12 }}>n={fmt(t.count)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* REPETITION BRIDGE */}
      <div style={{ marginBottom: 36, background: C.surfaceDeep, border: `1px solid ${C.border}`, borderRadius: 12, padding: 28 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 9, fontWeight: 600, color: C.green, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 8 }}>The repetition bridge</div>
          <div style={{ fontSize: 17, fontWeight: 600, color: C.white, fontStyle: 'italic' }}>"Users listen to the same music repeatedly"</div>
          <div style={{ fontSize: 11, color: C.muted, marginTop: 6, maxWidth: 560, marginLeft: 'auto', marginRight: 'auto', lineHeight: 1.5 }}>
            {fmt(br.total)} reviews describe hearing the same music repeatedly. In this data the split is almost entirely one way: users are not choosing to repeat, the app imposes it.
          </div>
          <div style={{ width: 1, height: 20, background: C.borderSubtle, margin: '14px auto 0' }} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <BridgeCard data={br.chosen} color={C.green} faint="Virtually absent. Users almost never frame repeated listening as a chosen comfort; in this data the repetition is something the app imposes." />
          <BridgeCard data={br.imposed} color={C.red} faint="" />
        </div>
      </div>

      {/* NEXT */}
      <div style={{ padding: '16px 20px', background: 'rgba(88,166,255,0.05)', border: '1px solid rgba(88,166,255,0.15)', borderRadius: 8, fontSize: 12, color: C.text2, lineHeight: 1.6 }}>
        <span style={{ color: C.blue, fontWeight: 600 }}>Next {'→'}</span> Every theme, need, and segment above is a claim. The reader who wants to verify any of them clicks through to the evidence.
      </div>
    </>
  );
}
