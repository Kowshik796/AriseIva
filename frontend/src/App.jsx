import React, { useState } from 'react';
import Navbar from './components/Navbar.jsx';
import SpeechToISL from './pages/SpeechToISL.jsx';
import SignToSpeech from './pages/SignToSpeech.jsx';

export default function App() {
  const [mode, setMode] = useState('speech-to-isl');

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100vh', overflow: 'hidden',
      background: '#03070d', color: '#d6eeff',
      fontFamily: "'DM Sans', sans-serif",
    }}>

      {/* Grid background */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        backgroundImage: [
          'linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)',
        ].join(','),
        backgroundSize: '40px 40px',
      }} />

      {/* Ambient glow blobs */}
      <div style={{
        position: 'fixed', top: '-10%', left: '-5%', pointerEvents: 'none', zIndex: 0,
        width: '40vw', height: '40vw',
        background: 'radial-gradient(circle, rgba(0,212,255,0.04) 0%, transparent 70%)',
      }} />
      <div style={{
        position: 'fixed', bottom: '-10%', right: '-5%', pointerEvents: 'none', zIndex: 0,
        width: '40vw', height: '40vw',
        background: 'radial-gradient(circle, rgba(124,58,237,0.05) 0%, transparent 70%)',
      }} />

      {/* Navbar */}
      <div style={{ position: 'relative', zIndex: 10 }}>
        <Navbar mode={mode} onModeChange={setMode} />
      </div>

      {/* Page content */}
      <main style={{ flex: 1, overflow: 'hidden', position: 'relative', zIndex: 10 }}>
        {mode === 'speech-to-isl'
          ? <SpeechToISL />
          : <SignToSpeech />
        }
      </main>

      {/* Bottom bar */}
      <div style={{
        position: 'relative', zIndex: 10,
        height: '24px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', padding: '0 24px',
        background: '#040a13', borderTop: '1px solid #0a1628',
      }}>
        <span style={{
          color: '#1d3a5a', fontSize: '10px',
          letterSpacing: '0.2em', textTransform: 'uppercase',
          fontFamily: "'DM Mono', monospace",
        }}>
          Arise IVA — Indian Sign Language AI System
        </span>
        <span style={{
          color: '#1d3a5a', fontSize: '10px',
          fontFamily: "'DM Mono', monospace",
        }}>
          ISL v2.1 · Backend :5000
        </span>
      </div>
    </div>
  );
}