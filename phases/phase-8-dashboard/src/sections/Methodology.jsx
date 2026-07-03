import React from 'react';
import { C, fmt } from '../tokens.js';

const Stage = ({ n, title, metric, metricLabel, children }) => (
  <div style={{ display: 'flex', gap: 22, marginBottom: 40 }}>
    <div style={{ flexShrink: 0, width: 44, textAlign: 'center' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.green, border: `1px solid rgba(29,185,84,0.35)`, background: 'rgba(29,185,84,0.06)', borderRadius: 8, width: 38, height: 38, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto' }}>{n}</div>
      <div style={{ width: 1, background: C.border, height: 'calc(100% - 30px)', margin: '8px auto 0' }} />
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 16, marginBottom: 12 }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: C.white, letterSpacing: '-0.01em' }}>{title}</div>
        {metric != null && (
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: C.white, letterSpacing: '-0.03em' }}>{metric}</div>
            {metricLabel && <div style={{ fontSize: 10, color: C.muted }}>{metricLabel}</div>}
          </div>
        )}
      </div>
      {children}
    </div>
  </div>
);

// What we did / Why we did it / How we checked — razor-sharp, one line each
const WWH = ({ what, why, check }) => (
  <div style={{ marginBottom: 16, maxWidth: 780 }}>
    {[['What we did', what], ['Why we did it', why], ['How we checked', check]].filter(([, v]) => v).map(([label, val]) => (
      <div key={label} style={{ display: 'flex', gap: 14, padding: '5px 0' }}>
        <div style={{ width: 116, flexShrink: 0, fontSize: 10.5, fontWeight: 600, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.4, paddingTop: 2 }}>{label}</div>
        <div style={{ fontSize: 13, color: C.text2, lineHeight: 1.5 }}>{val}</div>
      </div>
    ))}
  </div>
);

const Proof = ({ label, children }) => (
  <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: '16px 20px' }}>
    <div style={{ fontSize: 10, fontWeight: 600, color: C.green, letterSpacing: 0.5, textTransform: 'uppercase', marginBottom: 12 }}>✓ {label}</div>
    {children}
  </div>
);

const Header = () => (
  <div style={{ marginBottom: 36 }}>
    <div style={{ fontSize: 10, fontWeight: 600, color: C.muted, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 8 }}>Methodology</div>
    <div style={{ fontSize: 24, fontWeight: 700, color: C.white, letterSpacing: '-0.02em' }}>How this was built</div>
    <div style={{ fontSize: 13, color: C.text2, marginTop: 6 }}>One review, from raw scrape to coded insight, with the check behind each step.</div>
  </div>
);

const FieldIntegrity = ({ ev }) => (
  <Proof label="Field integrity">
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${ev.fieldIntegrity.length}, 1fr)`, gap: 12 }}>
      {ev.fieldIntegrity.map((fi) => (
        <div key={fi.field} style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14, textAlign: 'center' }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: fi.valid >= 99 ? C.green : C.amber, letterSpacing: '-0.03em' }}>{fi.valid}%</div>
          <div style={{ fontSize: 11, color: C.text2, marginTop: 4 }}>{fi.field}</div>
          <div style={{ fontSize: 9, color: C.muted, marginTop: 4 }}>{fi.quarantined === 0 ? 'none quarantined' : `${fi.quarantined} quarantined`}</div>
        </div>
      ))}
    </div>
  </Proof>
);

const ConfusionMatrix = ({ cf, headline }) => {
  const maxCell = Math.max(...cf.matrix.flat(), 1);
  const short = (l) => (l.length > 5 ? l.slice(0, 4) + '.' : l);
  return (
    <>
      {headline}
      <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', marginBottom: 4, marginLeft: 60 }}>
          {cf.labels.map((l) => <div key={l} style={{ width: 26, textAlign: 'center', fontSize: 8, color: C.text2 }}>{short(l)}</div>)}
        </div>
        {cf.matrix.map((row, ri) => (
          <div key={ri} style={{ display: 'flex', alignItems: 'center', marginBottom: 2 }}>
            <div style={{ width: 58, textAlign: 'right', paddingRight: 6, fontSize: 8, color: C.text2 }}>{short(cf.labels[ri])}</div>
            {row.map((val, ci) => {
              const diag = ri === ci; const a = val / maxCell;
              const bg = val === 0 ? 'transparent' : diag ? `rgba(29,185,84,${(0.2 + a * 0.8).toFixed(2)})` : `rgba(248,81,73,${(0.15 + a * 0.6).toFixed(2)})`;
              return <div key={ci} style={{ width: 24, height: 20, margin: 1, borderRadius: 3, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 600, background: bg, color: val === 0 ? C.borderSubtle : diag ? (a > 0.5 ? '#04130a' : C.green) : C.red }}>{val || ''}</div>;
            })}
          </div>
        ))}
      </div>
    </>
  );
};

const SnapshotStage = ({ n }) => (
  <Stage n={n} title="Snapshot and contract" metric="✓" metricLabel="schema-valid">
    <WWH
      what="Computed every number once into a single JSON snapshot."
      why="A binding schema keeps the dashboard from drifting away from the pipeline."
      check="Cross-checks run before the snapshot ships." />
    <Proof label="Contract cross-checks, all passing">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 24px' }}>
        {['The funnel conserves at every step', 'Every sub-theme a bucket references exists', 'The star baseline sums to 100%', 'Every quote maps to a real discovery theme'].map((c) => (
          <div key={c} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ color: C.green, fontSize: 12, flexShrink: 0, fontWeight: 700 }}>✓</div>
            <div style={{ fontSize: 12, color: C.text2, lineHeight: 1.5 }}>{c}</div>
          </div>
        ))}
      </div>
    </Proof>
  </Stage>
);

const Limitations = ({ d, n }) => (
  <div style={{ display: 'flex', gap: 22 }}>
    <div style={{ flexShrink: 0, width: 44, textAlign: 'center' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.red, border: `1px solid rgba(248,81,73,0.35)`, background: 'rgba(248,81,73,0.06)', borderRadius: 8, width: 38, height: 38, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto' }}>{n}</div>
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 18, fontWeight: 700, color: C.white, letterSpacing: '-0.01em', marginBottom: 14 }}>Limitations, stated plainly</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 24px' }}>
        {d.limitations.map((l, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '6px 0' }}>
            <div style={{ color: C.red, fontSize: 7, marginTop: 6, flexShrink: 0 }}>●</div>
            <div style={{ fontSize: 12, color: C.text2, lineHeight: 1.5 }}>{l}</div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// ============================================================ iOS methodology
function IosMethodology({ d }) {
  const f = d.funnel;
  const ev = d.evaluation;
  const m = d.methodology;
  const rec = m.recovery;

  return (
    <>
      <Header />

      {/* 1 COLLECT */}
      <Stage n="01" title="Collect" metric={fmt(f.collected)} metricLabel="reviews scraped">
        <WWH
          what="Pulled Spotify's iTunes RSS review feed across US, GB, CA, IN, and AU, mostrecent sort only."
          why="The RSS feed hard-caps at ~500 reviews per storefront, so iOS is a current snapshot (~2-3 weeks), not a time series. mosthelpful was dropped: it spans years and skews the star mix."
          check="Five markets were kept by a scout that required 500 reviews to land inside ~3 weeks and be majority English." />
      </Stage>

      {/* 2 CLEAN */}
      <Stage n="02" title="Clean" metric={`${fmt(f.deduplicated)} → ${fmt(f.english)}`} metricLabel="unique, then English">
        <WWH
          what="De-duplicated on review id, then filtered to English with a lenient Latin-script fallback."
          why="iOS review ids are genuinely per-storefront (zero cross-country duplicates, unlike Android's collapsed global stream), so country is a real dimension here."
          check="Funnel reconciles at every step: in equals out plus removed." />
      </Stage>

      {/* 3 FILTER */}
      <Stage n="03" title="Filter to substance" metric={fmt(f.substantiveCensus)} metricLabel="substantive reviews">
        <WWH
          what="Removed only obvious junk (emoji-only, single words, spam) and passed borderline praise through."
          why="A word-count gate would drop 'shuffle isn't random' and keep empty rambles. The model judges substance later."
          check="Every field is validated against a typed schema, none silently coerced." />
        <FieldIntegrity ev={ev} />
      </Stage>

      {/* 4 CENSUS CLASSIFY (no sampling) */}
      <Stage n="04" title="Classify every review (census)" metric={fmt(f.sampled)} metricLabel="classified, no sampling">
        <WWH
          what={<><code style={{ color: C.text, fontSize: 12 }}>llama-3.1-8b-instant</code> tagged all {fmt(f.sampled)} substantive candidates with one to three categories and a sentiment. No sampling: iOS is small enough to run the whole census.</>}
          why={<>The paid LLM step is cheap at this scale, so iOS gets exact counts instead of sample estimates. Pricing leads at {d.categories[0].pct}%, discovery is second at {d.categories.find((c) => c.id === 'discovery').pct}%.</>}
          check="The classifier is the identical hardened prompt used on Android (same v5 tenets, ads-to-pricing, vague-praise-to-none), so the two tracks' categories mean the same thing." />
      </Stage>

      {/* 5 RECALL RECOVERY */}
      <Stage n="05" title="Recover missed discovery" metric={`+${rec.recovered}`} metricLabel="recovered on 120B">
        <WWH
          what={<>Ran <code style={{ color: C.text, fontSize: 12 }}>gpt-oss-120b</code> over the full ux and updates piles to catch discovery reviews the 8B filed elsewhere.</>}
          why="The 8B's discovery misses concentrate in ux and updates; a census of just those two piles recovers them cheaply on a separate rate-limit pool."
          check={`${rec.recovered} real discovery reviews recovered, lifting the pool from ${rec.origPool} to ${rec.finalPool}.`} />
        <Proof label="Recovery census (ux + updates)">
          {Object.entries(rec.perPile).map(([pile, v]) => (
            <div key={pile} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0', borderTop: `1px solid ${C.border}` }}>
              <div style={{ flex: 1, fontSize: 12, color: C.text, textTransform: 'capitalize' }}>{pile}</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.green }}>{v.missed}/{v.total}</div>
              <div style={{ fontSize: 10, color: C.muted, width: 90, textAlign: 'right' }}>actually discovery ({v.rate}%)</div>
            </div>
          ))}
        </Proof>
      </Stage>

      {/* 6 DEEP-DIVE on inherited v3 */}
      <Stage n="06" title="Deep-code on the inherited v3 codebook" metric={fmt(d.discovery.deepCoded)} metricLabel="confirmed discovery">
        <WWH
          what={<>Re-coded the {rec.finalPool}-review discovery pool into sub-themes on <code style={{ color: C.text, fontSize: 12 }}>gpt-oss-120b</code>, against the same codebook v3 the Android track had already hardened.</>}
          why="iOS did not re-derive the codebook. Reusing Android's locked v3 (autoplay and safe already retired) keeps the two tracks directly comparable, so we only needed to check that it travels to iOS."
          check={<>A strict gate dropped {fmt(m.deepCode.dropped)} non-discovery reviews ({m.deepCode.dropRate}%, the 8B's known over-tag), confirming {fmt(m.deepCode.kept)}. A {m.gold.n}-review human gold set then validated the fit.</>} />

        <Proof label={`Gold-set validation (${m.gold.n} reviews, codebook v3)`}>
          <ConfusionMatrix
            cf={ev.confusion}
            headline={
              <div style={{ fontSize: 12, color: C.text2, marginBottom: 12, lineHeight: 1.5 }}>
                <span style={{ color: C.green, fontWeight: 600 }}>{m.gold.overlap}%</span> theme overlap, kappa {m.gold.kappa}, in line with the codebook's documented fuzzy-boundary ceiling. {m.gold.boundaryNote}
              </div>
            } />
          <div style={{ fontSize: 11, color: C.text2, marginTop: 12, lineHeight: 1.5, borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>
            Emerging stayed low, so v3 fits iOS without changes. The result replicates Android: <span style={{ color: C.text, fontWeight: 600 }}>loss of control is the number-one discovery complaint</span>, and repetition is app-imposed, not chosen.
          </div>
        </Proof>
      </Stage>

      {/* 7 SNAPSHOT */}
      <SnapshotStage n="07" />

      {/* 8 LIMITATIONS */}
      <Limitations d={d} n="08" />
    </>
  );
}

// ============================================================ Android methodology
function AndroidMethodology({ d }) {
  const f = d.funnel;
  const ev = d.evaluation;
  const m = d.methodology;
  const maxSamp = Math.max(...ev.sampling.bars.flatMap((b) => [b.collected, b.store]), 1);

  return (
    <>
      <Header />

      {/* 1 COLLECT */}
      <Stage n="01" title="Collect" metric={fmt(f.collected)} metricLabel="reviews scraped">
        <WWH
          what="Scraped Spotify's full Google Play review feed across US, GB, and IN over six months, streamed to disk."
          why="Six months of history separates a structural complaint from a spike tied to one app update."
          check="We took a census of the NEWEST feed, not a sorted slice, so the collected star mix matches the store." />
        <Proof label="Sampling fairness">
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 18, height: 100, padding: '0 4px' }}>
            {ev.sampling.bars.map((b) => (
              <div key={b.stars} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, height: '100%', justifyContent: 'flex-end' }}>
                <div style={{ width: '100%', display: 'flex', gap: 4, alignItems: 'flex-end', height: 76, justifyContent: 'center' }}>
                  <div style={{ width: '38%', background: C.muted, borderRadius: '3px 3px 0 0', height: `${(b.collected / maxSamp) * 100}%` }} />
                  <div style={{ width: '38%', background: C.green, borderRadius: '3px 3px 0 0', height: `${(b.store / maxSamp) * 100}%` }} />
                </div>
                <div style={{ fontSize: 10, color: C.text2 }}>{b.stars}★</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 10, color: C.text2 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><div style={{ width: 9, height: 9, background: C.muted, borderRadius: 2 }} />Collected</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}><div style={{ width: 9, height: 9, background: C.green, borderRadius: 2 }} />Store-representative</div>
          </div>
        </Proof>
      </Stage>

      {/* 2 CLEAN */}
      <Stage n="02" title="Clean" metric={`${fmt(f.deduplicated)} → ${fmt(f.english)}`} metricLabel="unique, then English">
        <WWH
          what="De-duplicated on review id, then filtered to English with a lenient Latin-script fallback."
          why="Play returns one global stream per country, so the raw pull is about three copies. Dedup first stops duplicates triple-counting the star baseline, and the lenient filter keeps Hinglish and slang." />
      </Stage>

      {/* 3 FILTER */}
      <Stage n="03" title="Filter to substance" metric={fmt(f.substantiveCensus)} metricLabel="substantive reviews">
        <WWH
          what="Removed only obvious junk (emoji-only, single words, spam) and passed borderline praise through."
          why="A word-count gate would drop 'shuffle isn't random' and keep empty rambles. The model judges substance later."
          check="Every field is validated against a typed schema, none silently coerced." />
        <FieldIntegrity ev={ev} />
      </Stage>

      {/* 4 CENSUS VS SAMPLE */}
      <Stage n="04" title="Census vs sample" metric={fmt(f.sampled)} metricLabel="stratified sample">
        <WWH
          what="Ran free stats on the full population and sampled only the paid LLM step."
          why="The project runs on a free inference tier, so census stays exact and only classification needs a sample."
          check="Stratified by month, 2,000 to 4,000 per month scaled to volume, with a floor and cap so no month dominates." />
      </Stage>

      {/* 5 BROAD PASS */}
      <Stage n="05" title="Broad classification (Layer-1)" metric={`${fmt(f.sampled)} → ${fmt(f.contentBearing)}`} metricLabel="classified, content-bearing">
        <WWH
          what={<><code style={{ color: C.text, fontSize: 12 }}>llama-3.1-8b-instant</code> tagged each review with one to three categories and a sentiment. {fmt(f.contentBearing)} carried real content; the rest routed to "none".</>}
          why={<>A cheap broad pass sizes every category at once. Pricing leads at 52.8%, discovery is second at 17.8% ({fmt(d.discovery.sampleN)} reviews).</>}
          check={<>A recall probe on <code style={{ color: C.text, fontSize: 12 }}>gpt-oss-120b</code> measured how many discovery reviews the 8B missed.</>} />
        <Proof label="Discovery recall probe">
          <div style={{ display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: 30, fontWeight: 700, color: C.green, letterSpacing: '-0.03em' }}>{m.recallProbe.rate}%</div>
              <div style={{ fontSize: 11, color: C.text2 }}>false-negative rate (±{m.recallProbe.ci}%)</div>
            </div>
            <div style={{ fontSize: 12, color: C.text2, lineHeight: 1.6, flex: 1, minWidth: 240 }}>{m.recallProbe.missed} of {m.recallProbe.probed} non-discovery reviews were actually discovery. The 8B over-tags discovery, the safe direction, since the deep pass filters the excess.</div>
          </div>
        </Proof>
      </Stage>

      {/* 6 DEEP-DIVE */}
      <Stage n="06" title="Deep-dive, and the codebook that corrected itself" metric={fmt(d.discovery.deepCoded)} metricLabel="confirmed discovery">
        <WWH
          what={<>Re-coded the discovery reviews into sub-themes on <code style={{ color: C.text, fontSize: 12 }}>gpt-oss-120b</code>.</>}
          why="Deep coding needs more reasoning than the broad pass, and runs on a separate rate-limit pool so the two never compete."
          check="A gold set exposed the fuzzy themes, a borderline test killed two of them, and v3 re-coded the pool." />

        {/* codebook timeline */}
        <div style={{ display: 'flex', alignItems: 'stretch', gap: 0, marginBottom: 18 }}>
          {m.codebook.map((c, i) => (
            <React.Fragment key={c.v}>
              <div style={{ flex: 1, background: i === 2 ? 'rgba(29,185,84,0.06)' : C.surface, border: `1px solid ${i === 2 ? 'rgba(29,185,84,0.3)' : C.border}`, borderRadius: 10, padding: 16 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
                  <div style={{ fontSize: 15, fontWeight: 700, color: i === 2 ? C.green : C.white }}>{c.v}</div>
                  <div style={{ fontSize: 11, color: C.muted }}>{c.themes} themes</div>
                </div>
                <div style={{ fontSize: 11, color: C.text2, lineHeight: 1.5 }}>{c.note}</div>
              </div>
              {i < m.codebook.length - 1 && <div style={{ display: 'flex', alignItems: 'center', padding: '0 8px', color: C.muted, fontSize: 16 }}>{'→'}</div>}
            </React.Fragment>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 20 }}>
          {/* 6a confusion matrix */}
          <Proof label="Gold-set validation (6a)">
            <ConfusionMatrix
              cf={ev.confusion}
              headline={<div style={{ fontSize: 12, color: C.text2, marginBottom: 12, lineHeight: 1.5 }}>50-review gold set, weighted to hard cases. <span style={{ color: C.green, fontWeight: 600 }}>{d.validation.themeAccuracy}%</span> overlap, kappa {d.validation.kappa}. The matrix exposed the fuzzy boundaries.</div>} />
          </Proof>

          {/* 6b borderline test */}
          <Proof label="Borderline test (6b) → drove v3">
            <div style={{ fontSize: 12, color: C.text2, marginBottom: 14, lineHeight: 1.5 }}>A blind re-label of the fuzziest themes. A human never kept autoplay or safe.</div>
            {m.borderline.tests.map((t) => {
              const kept = t.kept === 0; const col = kept ? C.red : C.green;
              return (
                <div key={t.name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0', borderTop: `1px solid ${C.border}` }}>
                  <div style={{ flex: 1, fontSize: 12, color: C.text }}>{t.name}</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: col }}>{t.kept}/{t.total}</div>
                  <div style={{ fontSize: 9, color: col, textTransform: 'uppercase', letterSpacing: 0.3, width: 54, textAlign: 'right' }}>{kept ? 'removed' : 'kept'}</div>
                </div>
              );
            })}
            <div style={{ fontSize: 11, color: C.text2, marginTop: 12, lineHeight: 1.5, borderTop: `1px solid ${C.border}`, paddingTop: 10 }}>v3 re-coded the pool on 120B: <span style={{ color: C.text, fontWeight: 600 }}>{fmt(m.v3recode.dropped)} dropped</span> ({m.v3recode.notDiscovery} not-discovery, {m.v3recode.language} non-English), <span style={{ color: C.green, fontWeight: 600 }}>{fmt(m.v3recode.deepCoded)} confirmed</span>.</div>
          </Proof>
        </div>
      </Stage>

      {/* 7 SNAPSHOT */}
      <SnapshotStage n="07" />

      {/* 8 LIMITATIONS */}
      <Limitations d={d} n="08" />
    </>
  );
}

export default function Methodology({ d, track }) {
  return track === 'ios' ? <IosMethodology d={d} /> : <AndroidMethodology d={d} />;
}
