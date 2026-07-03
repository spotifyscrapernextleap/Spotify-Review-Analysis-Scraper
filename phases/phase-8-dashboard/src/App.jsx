import React, { useState } from 'react';
import ANDROID_DATA from './review_data.android.json';
import IOS_DATA from './review_data.ios.json';
import { C } from './tokens.js';
import Overview from './sections/Overview.jsx';
import Discovery from './sections/Discovery.jsx';
import Evidence from './sections/Evidence.jsx';
import Methodology from './sections/Methodology.jsx';

const SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'discovery', label: 'Discovery Deep Dive' },
  { id: 'evidence', label: 'Evidence Explorer' },
  { id: 'methodology', label: 'Methodology & Evaluation' },
];

// iOS first per the design; Android is the established six-month track.
const TRACKS = [
  { id: 'ios', label: 'iOS', data: IOS_DATA, note: 'iOS track · current snapshot' },
  { id: 'android', label: 'Android', data: ANDROID_DATA, note: 'Android track · 6-month census' },
];

export default function App() {
  const [track, setTrack] = useState('android');
  const [activeSection, setActiveSection] = useState('overview');

  const t = TRACKS.find((x) => x.id === track);
  const d = t.data;

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* SIDEBAR */}
      <nav style={{ width: 236, background: C.sidebar, borderRight: `1px solid ${C.border}`,
        position: 'fixed', top: 0, left: 0, height: '100vh', display: 'flex', flexDirection: 'column', zIndex: 10 }}>
        <div style={{ padding: '28px 24px 16px' }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: C.green, letterSpacing: 2, textTransform: 'uppercase' }}>Review Intelligence</div>
          <div style={{ fontSize: 11, color: C.muted, marginTop: 4 }}>Spotify · Discovery Analysis</div>
        </div>

        {/* TRACK TOGGLE */}
        <div style={{ padding: '0 20px 16px' }}>
          <div style={{ display: 'flex', gap: 6, background: C.bg, border: `1px solid ${C.border}`, borderRadius: 8, padding: 4 }}>
            {TRACKS.map((x) => {
              const on = track === x.id;
              return (
                <div key={x.id} onClick={() => setTrack(x.id)}
                  style={{ flex: 1, textAlign: 'center', padding: '7px 0', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                    color: on ? '#04130a' : C.text2, background: on ? C.green : 'transparent',
                    borderRadius: 6, transition: 'all 0.12s' }}>
                  {x.label}
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ height: 1, background: C.border, margin: '0 16px' }} />
        <div style={{ padding: '12px 0', flex: 1 }}>
          {SECTIONS.map((s) => {
            const active = activeSection === s.id;
            return (
              <div key={s.id} onClick={() => setActiveSection(s.id)}
                style={{ padding: '10px 24px', cursor: 'pointer', fontSize: 13, fontWeight: 500,
                  color: active ? C.white : C.text2, background: active ? 'rgba(29,185,84,0.08)' : 'transparent',
                  borderLeft: `3px solid ${active ? C.green : 'transparent'}`, transition: 'all 0.12s' }}>
                {s.label}
              </div>
            );
          })}
        </div>
        <div style={{ padding: '16px 24px', borderTop: `1px solid ${C.border}` }}>
          <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.5 }}>{t.note}</div>
          <div style={{ fontSize: 10, color: C.borderSubtle, marginTop: 2 }}>{d.window.collection}</div>
        </div>
      </nav>

      {/* MAIN */}
      <main style={{ marginLeft: 236, flex: 1, padding: '36px 48px 80px', maxWidth: 1080 }}>
        {activeSection === 'overview' && <Overview d={d} track={track} />}
        {activeSection === 'discovery' && <Discovery d={d} track={track} />}
        {activeSection === 'evidence' && <Evidence d={d} track={track} />}
        {activeSection === 'methodology' && <Methodology d={d} track={track} />}
      </main>
    </div>
  );
}
