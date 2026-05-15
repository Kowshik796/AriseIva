import React from 'react';

export default function Navbar({ mode, onModeChange }) {
  return (
    <header style={{
      position: 'relative', height: '64px', display: 'flex', alignItems: 'center',
      padding: '0 24px', borderBottom: '1px solid #132240',
      background: 'linear-gradient(180deg, #080f1e 0%, #070d1a 100%)',
    }}>

      {/* Top accent line */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '1px',
        background: 'linear-gradient(90deg, transparent, #00d4ff, transparent)',
      }} />

      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', userSelect: 'none' }}>
        <div style={{
          width: '36px', height: '36px', display: 'flex', alignItems: 'center',
          justifyContent: 'center', borderRadius: '8px', fontSize: '18px',
          background: 'linear-gradient(135deg, rgba(0,212,255,0.15), rgba(124,58,237,0.15))',
          border: '1px solid rgba(0,212,255,0.3)',
          boxShadow: '0 0 12px rgba(0,212,255,0.2)',
        }}>
          〰
        </div>
        <div>
          <div style={{
            fontFamily: "'Exo 2', sans-serif", fontWeight: 700,
            fontSize: '15px', letterSpacing: '0.12em',
          }}>
            <span style={{ color: '#00d4ff', textShadow: '0 0 16px rgba(0,212,255,0.6)' }}>ARISE</span>
            <span style={{ color: '#d6eeff' }}> IVA</span>
          </div>
          <div style={{
            fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase',
            color: '#3d6080', fontFamily: "'DM Mono', monospace",
          }}>
            AI Sign Language System
          </div>
        </div>
      </div>

      {/* Center mode tabs */}
      <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
        <div style={{
          display: 'flex', alignItems: 'center', padding: '4px', borderRadius: '10px', gap: '4px',
          background: '#050c17', border: '1px solid #132240',
        }}>
          {[
            { id: 'speech-to-isl',  label: 'Speech → ISL', emoji: '🎙' },
            { id: 'sign-to-speech', label: 'Sign → Speech', emoji: '🤟' },
          ].map((tab) => {
            const active = mode === tab.id;
            return (
              <button key={tab.id} onClick={() => onModeChange(tab.id)}
                style={{
                  padding: '6px 16px', borderRadius: '7px', fontSize: '12px',
                  fontFamily: "'DM Sans', sans-serif", fontWeight: active ? 600 : 400,
                  cursor: 'pointer', transition: 'all 0.3s',
                  color: active ? '#00d4ff' : '#3d6080',
                  background: active ? 'rgba(0,212,255,0.1)' : 'transparent',
                  border: active ? '1px solid rgba(0,212,255,0.25)' : '1px solid transparent',
                  boxShadow: active ? '0 0 12px rgba(0,212,255,0.15)' : 'none',
                }}>
                <span style={{ marginRight: '6px' }}>{tab.emoji}</span>
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Right version tag */}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#3d6080', fontFamily: "'DM Mono', monospace" }}>
          v2.1.0
        </span>
      </div>
    </header>
  );
}