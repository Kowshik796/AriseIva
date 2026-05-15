import React, { useState, useCallback } from 'react';
import SignCamera      from '../components/SignCamera.jsx';
import SentenceBuilder from '../components/SentenceBuilder.jsx';
import StatusIndicators from '../components/StatusIndicators.jsx';

export default function SignToSpeech() {
  const [cameraActive,    setCameraActive]    = useState(false);
  const [detectedGesture, setDetectedGesture] = useState(null);

  // Wrapped in useCallback so SignCamera's useEffect dep-array stays stable
  const handleGestureDetected = useCallback((result) => {
    setDetectedGesture(result);
  }, []);

  const handleCameraStatus = useCallback((active) => {
    setCameraActive(active);
    if (!active) setDetectedGesture(null);
  }, []);

  const pct = detectedGesture ? Math.round(detectedGesture.confidence * 100) : 0;

  return (
    <div style={{ display:'flex', height:'100%' }}>

      {/* ════════════════════════════════════════════
          LEFT PANEL
      ════════════════════════════════════════════ */}
      <div style={{
        width:'320px', flexShrink:0, display:'flex', flexDirection:'column',
        gap:'14px', padding:'20px', overflowY:'auto',
        background:'#070d1a', borderRight:'1px solid #132240',
      }}>

        {/* Panel header */}
        <div style={{
          display:'flex', alignItems:'center', gap:'10px',
          paddingBottom:'12px', borderBottom:'1px solid #132240',
        }}>
          <div style={{ width:'4px', height:'20px', borderRadius:'2px', background:'#7c3aed', flexShrink:0 }} />
          <h2 style={{
            fontSize:'12px', letterSpacing:'0.25em', textTransform:'uppercase',
            color:'#7aa2c0', fontFamily:"'DM Mono', monospace", margin:0,
          }}>Sign → Speech</h2>
        </div>

        {/* Detected gesture card */}
        <div style={{
          padding:'14px 16px', borderRadius:'12px',
          background:'#050c17', border:'1px solid #132240',
        }}>
          <p style={{
            fontSize:'10px', letterSpacing:'0.25em', textTransform:'uppercase',
            color:'#3d6080', fontFamily:"'DM Mono', monospace", margin:'0 0 10px 0',
          }}>Detected Gesture</p>

          <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
            {/* Gesture name */}
            <div style={{
              flex:1, height:'42px', borderRadius:'8px', padding:'0 14px',
              display:'flex', alignItems:'center',
              background:'#040b14',
              border: detectedGesture
                ? '1px solid rgba(0,212,255,0.35)'
                : '1px solid #132240',
              transition:'border-color 0.3s',
            }}>
              {detectedGesture ? (
                <span style={{
                  fontSize:'18px', fontWeight:800,
                  fontFamily:"'Exo 2', sans-serif",
                  color:'#00d4ff',
                  textShadow:'0 0 14px rgba(0,212,255,0.55)',
                  letterSpacing:'0.08em',
                }}>
                  {detectedGesture.gesture}
                </span>
              ) : (
                <span style={{ fontSize:'12px', color:'#1d3a5a', fontFamily:"'DM Mono', monospace" }}>
                  Waiting for sign…
                </span>
              )}
            </div>

            {/* Confidence badge */}
            {detectedGesture && (
              <div style={{
                padding:'6px 10px', borderRadius:'8px', flexShrink:0,
                display:'flex', flexDirection:'column', alignItems:'center', gap:'3px',
                background: pct >= 70 ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                border: `1px solid ${pct >= 70 ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
              }}>
                <div style={{
                  width:'6px', height:'6px', borderRadius:'50%',
                  background: pct >= 70 ? '#10b981' : '#f59e0b',
                }} />
                <span style={{
                  fontSize:'12px', fontWeight:700, fontFamily:"'DM Mono', monospace",
                  color: pct >= 70 ? '#10b981' : '#f59e0b',
                }}>
                  {pct}%
                </span>
              </div>
            )}
          </div>

          {/* Mini confidence bar */}
          {detectedGesture && (
            <div style={{ marginTop:'10px', height:'4px', borderRadius:'2px', background:'#132240', overflow:'hidden' }}>
              <div style={{
                height:'100%', borderRadius:'2px', transition:'width 0.4s ease',
                width:`${pct}%`,
                background: pct >= 80
                  ? 'linear-gradient(90deg,#10b981,#00d4ff)'
                  : pct >= 60
                  ? 'linear-gradient(90deg,#f59e0b,#10b981)'
                  : '#ef4444',
              }} />
            </div>
          )}
        </div>

        {/* Sentence builder — receives detected gesture */}
        <SentenceBuilder detectedGesture={detectedGesture} />

        <div style={{ flex:1 }} />

        {/* Status indicators */}
        <StatusIndicators cameraActive={cameraActive} />
      </div>

      {/* ════════════════════════════════════════════
          RIGHT PANEL — Camera
      ════════════════════════════════════════════ */}
      <div style={{
        flex:1, padding:'24px', overflow:'hidden',
        backgroundImage: [
          'linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px)',
          'linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)',
        ].join(','),
        backgroundSize:'40px 40px',
      }}>
        <div style={{ height:'100%', display:'flex', flexDirection:'column' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'16px' }}>
            <p style={{
              fontSize:'11px', letterSpacing:'0.3em', textTransform:'uppercase',
              color:'#3d6080', fontFamily:"'DM Mono', monospace", margin:0,
            }}>Live Camera Feed</p>
            {cameraActive && (
              <span style={{
                fontSize:'10px', padding:'3px 10px', borderRadius:'4px',
                background:'rgba(16,185,129,0.1)', border:'1px solid rgba(16,185,129,0.25)',
                color:'#10b981', fontFamily:"'DM Mono', monospace",
              }}>● STREAMING</span>
            )}
          </div>
          <div style={{ flex:1 }}>
            <SignCamera
              onCameraStatusChange={handleCameraStatus}
              onGestureDetected={handleGestureDetected}
            />
          </div>
        </div>
      </div>
    </div>
  );
}