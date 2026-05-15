import React, { useState, useCallback } from 'react';
import SpeechInput      from '../components/SpeechInput.jsx';
import ISLPlayer        from '../components/ISLPlayer.jsx';
import StatusIndicators from '../components/StatusIndicators.jsx';
import { speechToISL }  from '../api/ariseApi.js';

export default function SpeechToISL() {
  const [loading,       setLoading]       = useState(false);
  const [glosses,       setGlosses]       = useState([]);
  const [skipped,       setSkipped]       = useState([]);
  const [lastInput,     setLastInput]     = useState('');
  const [error,         setError]         = useState('');
  const [activeGlossIdx, setActiveGlossIdx] = useState(-1);  // highlighted gloss index

  const handleConvert = async (text) => {
    setLoading(true);
    setError('');
    setLastInput(text);
    setGlosses([]);
    setSkipped([]);
    setActiveGlossIdx(-1);

    try {
      const result = await speechToISL(text);
      setGlosses(result.gloss       || []);
      setSkipped(result.skipped      || []);
    } catch (err) {
      const msg = err?.response?.data?.error
        || 'Could not reach ISL backend on port 8000.';
      setError(msg);
      setGlosses(text.toUpperCase().split(' ').filter(Boolean));
      setSkipped([]);
    } finally {
      setLoading(false);
    }
  };

  // Fired by ISLPlayer whenever the active sign changes
  const handleTokenChange = useCallback((glossIdx) => {
    setActiveGlossIdx(glossIdx);
  }, []);

  return (
    <div style={{ display: 'flex', height: '100%' }}>

      {/* ══ LEFT PANEL ═══════════════════════════════════════════════ */}
      <div style={{
        width: '320px', flexShrink: 0,
        display: 'flex', flexDirection: 'column', gap: '14px',
        padding: '20px', overflowY: 'auto',
        background: '#070d1a', borderRight: '1px solid #132240',
      }}>

        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          paddingBottom: '12px', borderBottom: '1px solid #132240',
        }}>
          <div style={{ width: '4px', height: '20px', borderRadius: '2px', background: '#00d4ff' }} />
          <h2 style={{
            fontSize: '12px', letterSpacing: '0.25em', textTransform: 'uppercase',
            color: '#7aa2c0', fontFamily: "'DM Mono', monospace", margin: 0,
          }}>Speech → ISL</h2>
        </div>

        <SpeechInput onConvert={handleConvert} loading={loading} />

        {/* Gloss output panel */}
        {glosses.length > 0 && (
          <div style={{
            borderRadius: '12px', padding: '16px',
            background: '#050c17', border: '1px solid #132240',
          }}>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', marginBottom: '12px',
            }}>
              <p style={{
                fontSize: '10px', letterSpacing: '0.25em', textTransform: 'uppercase',
                color: '#7aa2c0', fontFamily: "'DM Mono', monospace", margin: 0,
              }}>📖 ISL Gloss</p>
              <span style={{ fontSize: '10px', color: '#10b981' }}>✓</span>
            </div>

            {/* Input echo */}
            {lastInput && (
              <div style={{ paddingBottom: '10px', marginBottom: '10px', borderBottom: '1px solid #0a1628' }}>
                <p style={{ fontSize: '10px', color: '#3d6080', fontFamily: "'DM Mono', monospace", margin: '0 0 3px 0' }}>INPUT</p>
                <p style={{ fontSize: '12px', fontStyle: 'italic', color: '#7aa2c0', margin: 0 }}>
                  "{lastInput}"
                </p>
              </div>
            )}

            {/* Gloss chips — active one glows */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {glosses.map((g, i) => {
                const isActive  = i === activeGlossIdx;
                const isSkipped = skipped.includes(g);
                return (
                  <span key={i} style={{
                    padding: '5px 10px', borderRadius: '7px',
                    fontSize: '11px', fontWeight: 700, letterSpacing: '0.08em',
                    fontFamily: "'Exo 2', sans-serif",
                    transition: 'all 0.25s ease',
                    background: isActive
                      ? 'rgba(0,212,255,0.22)'
                      : isSkipped
                      ? 'rgba(239,68,68,0.06)'
                      : 'rgba(0,212,255,0.07)',
                    border: isActive
                      ? '1px solid rgba(0,212,255,0.7)'
                      : isSkipped
                      ? '1px solid rgba(239,68,68,0.2)'
                      : '1px solid rgba(0,212,255,0.18)',
                    color: isActive
                      ? '#00d4ff'
                      : isSkipped
                      ? '#7a4040'
                      : '#5a9ab5',
                    boxShadow: isActive
                      ? '0 0 12px rgba(0,212,255,0.4)'
                      : 'none',
                    transform: isActive ? 'scale(1.05)' : 'scale(1)',
                  }}>
                    {g}
                    {isSkipped && (
                      <span style={{ fontSize: '8px', marginLeft: '3px', opacity: 0.5 }}>✕</span>
                    )}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Error notice */}
        {error && (
          <div style={{
            padding: '10px 14px', borderRadius: '10px', fontSize: '11px',
            background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)',
            color: '#f59e0b',
          }}>ℹ {error}</div>
        )}

        <div style={{ flex: 1 }} />
        <StatusIndicators cameraActive={false} />
      </div>

      {/* ══ RIGHT PANEL — ISL Video Player ════════════════════════════ */}
      <div style={{
        flex: 1, padding: '24px', overflow: 'hidden',
        backgroundImage: [
          'linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)',
        ].join(','),
        backgroundSize: '40px 40px',
      }}>
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '16px' }}>
            <p style={{
              fontSize: '11px', letterSpacing: '0.3em', textTransform: 'uppercase',
              color: '#3d6080', fontFamily: "'DM Mono', monospace", margin: 0,
            }}>ISL Sign Player</p>
          </div>
          <div style={{ flex: 1 }}>
            <ISLPlayer
              glosses={glosses}
              onTokenChange={handleTokenChange}
            />
          </div>
        </div>
      </div>
    </div>
  );
}