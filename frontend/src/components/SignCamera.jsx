import React, { useRef, useEffect, useState, useCallback } from 'react';
import { predictGesture } from '../api/ariseApi.js';

// ── Tuning constants ──────────────────────────────────────────────────────────
const CAPTURE_INTERVAL_MS  = 500;   // capture every 500ms
const STABILITY_THRESHOLD  = 3;     // same gesture must appear 3× in a row before firing
const MIN_HUD_CONFIDENCE   = 0.45;  // show on HUD above this
const FIRE_CONFIDENCE      = 0.70;  // send to sentence builder above this

export default function SignCamera({ onCameraStatusChange, onGestureDetected }) {
  const videoRef    = useRef(null);
  const canvasRef   = useRef(null);
  const streamRef   = useRef(null);
  const intervalRef = useRef(null);

  // Stability buffer: tracks last N consecutive predictions
  const stabilityRef = useRef({ gesture: '', count: 0, firedAt: 0 });

  const [active,     setActive]     = useState(false);
  const [prediction, setPrediction] = useState(null);   // shown on HUD
  const [error,      setError]      = useState('');
  const [scanPos,    setScanPos]    = useState(0);
  const [stableCount, setStableCount] = useState(0);    // visual indicator

  // Scan line animation
  useEffect(() => {
    if (!active) return;
    let pos = 0;
    const id = setInterval(() => { pos = (pos + 0.8) % 100; setScanPos(pos); }, 30);
    return () => clearInterval(id);
  }, [active]);

  const captureFrame = useCallback(() => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return null;
    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    // ✅ Raw frame — no mirroring. CSS handles display mirror only.
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
  }, []);

  const startPredictionLoop = useCallback(() => {
    intervalRef.current = setInterval(async () => {
      const frame = captureFrame();
      if (!frame) return;

      try {
        const result = await predictGesture(frame);
        const gesture    = result?.gesture;
        const confidence = result?.confidence ?? 0;

        // ── Update HUD ────────────────────────────────────────────────────────
        if (gesture && confidence >= MIN_HUD_CONFIDENCE) {
          setPrediction(result);
        } else {
          setPrediction(null);
          stabilityRef.current = { gesture: '', count: 0, firedAt: stabilityRef.current.firedAt };
          setStableCount(0);
          return;
        }

        // ── Stability buffer ──────────────────────────────────────────────────
        // Only send to sentence if the SAME gesture appears STABILITY_THRESHOLD
        // times consecutively AND confidence is high enough.
        const sb = stabilityRef.current;

        if (gesture === sb.gesture) {
          const newCount = sb.count + 1;
          stabilityRef.current.count = newCount;
          setStableCount(newCount);

          // Fire only once per stable lock-in (not every subsequent frame)
          if (newCount === STABILITY_THRESHOLD && confidence >= FIRE_CONFIDENCE) {
            stabilityRef.current.firedAt = Date.now();
            onGestureDetected({ gesture, confidence });
          }
        } else {
          // Different gesture — reset streak
          stabilityRef.current = { gesture, count: 1, firedAt: sb.firedAt };
          setStableCount(1);
        }

      } catch {
        setPrediction(null);
        stabilityRef.current = { gesture: '', count: 0, firedAt: 0 };
        setStableCount(0);
      }
    }, CAPTURE_INTERVAL_MS);
  }, [captureFrame, onGestureDetected]);

  const startCamera = async () => {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
      onCameraStatusChange(true);
      startPredictionLoop();
    } catch (err) {
      setError(
        err.name === 'NotAllowedError'
          ? 'Camera permission denied. Please allow camera access.'
          : 'Could not access camera. Make sure it is connected.'
      );
      onCameraStatusChange(false);
    }
  };

  const stopCamera = useCallback(() => {
    clearInterval(intervalRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    stabilityRef.current = { gesture: '', count: 0, firedAt: 0 };
    setActive(false);
    setPrediction(null);
    setStableCount(0);
    onCameraStatusChange(false);
  }, [onCameraStatusChange]);

  useEffect(() => () => stopCamera(), [stopCamera]);

  const pct = prediction ? Math.round(prediction.confidence * 100) : 0;
  const barColor =
    pct >= 80 ? 'linear-gradient(90deg,#10b981,#00d4ff)' :
    pct >= 60 ? 'linear-gradient(90deg,#f59e0b,#10b981)' : '#ef4444';

  // Stability dots — shows how many consecutive matches so far
  const stabilityDots = Array.from({ length: STABILITY_THRESHOLD }, (_, i) => i < stableCount);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* ── Viewport ─────────────────────────────────────── */}
      <div style={{
        flex: 1, minHeight: '320px', borderRadius: '16px', position: 'relative',
        background: '#040b14', overflow: 'hidden',
        border: active ? '1px solid rgba(0,212,255,0.35)' : '1px solid #132240',
        boxShadow: active ? '0 0 32px rgba(0,212,255,0.08)' : 'none',
      }}>

        {/* Corner brackets */}
        {[
          { top:0,    left:0,  borderTop:'2px solid',    borderLeft:'2px solid'   },
          { top:0,    right:0, borderTop:'2px solid',    borderRight:'2px solid'  },
          { bottom:0, left:0,  borderBottom:'2px solid', borderLeft:'2px solid'   },
          { bottom:0, right:0, borderBottom:'2px solid', borderRight:'2px solid'  },
        ].map((s, i) => (
          <div key={i} style={{
            position: 'absolute', width: '22px', height: '22px', zIndex: 4,
            borderColor: active ? 'rgba(0,212,255,0.6)' : 'rgba(0,212,255,0.2)', ...s,
          }} />
        ))}

        {/* Video — CSS mirror for display only */}
        <video ref={videoRef} muted playsInline style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', transform: 'scaleX(-1)',
          display: active ? 'block' : 'none',
        }} />

        {/* Hidden canvas for raw frame capture */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Scan line */}
        {active && (
          <div style={{
            position: 'absolute', left: 0, right: 0, height: '2px',
            top: `${scanPos}%`, zIndex: 3, pointerEvents: 'none',
            background: 'linear-gradient(90deg,transparent,rgba(0,212,255,0.5),transparent)',
            filter: 'blur(1px)',
          }} />
        )}

        {/* Idle state */}
        {!active && (
          <div style={{
            position: 'absolute', inset: 0,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: '14px',
          }}>
            <div style={{ fontSize: '52px', opacity: 0.12 }}>📷</div>
            <p style={{
              fontSize: '11px', letterSpacing: '0.25em', textTransform: 'uppercase',
              color: '#3d6080', fontFamily: "'DM Mono', monospace",
            }}>Camera Offline</p>
          </div>
        )}

        {/* Label */}
        <div style={{
          position: 'absolute', top: '12px', left: '12px', zIndex: 5,
          padding: '3px 8px', borderRadius: '4px',
          background: 'rgba(0,0,0,0.65)', border: '1px solid #132240',
          fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase',
          color: '#3d6080', fontFamily: "'DM Mono', monospace",
        }}>CAMERA FEED</div>

        {/* LIVE badge */}
        {active && (
          <div style={{
            position: 'absolute', top: '12px', right: '12px', zIndex: 5,
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '4px 10px', borderRadius: '4px',
            background: 'rgba(3,7,13,0.82)', border: '1px solid rgba(0,212,255,0.35)',
            fontSize: '10px', color: '#00d4ff', fontFamily: "'DM Mono', monospace",
          }}>
            <span style={{ animation: 'blink 1.2s ease-in-out infinite' }}>●</span> LIVE
          </div>
        )}

        {/* ── Gesture HUD ──────────────────────────────────── */}
        {active && (
          <div style={{
            position: 'absolute', bottom: '14px', left: '14px', right: '14px', zIndex: 5,
            borderRadius: '12px', padding: '12px 16px',
            background: 'rgba(3,7,13,0.9)',
            border: prediction
              ? '1px solid rgba(0,212,255,0.4)'
              : '1px solid rgba(255,255,255,0.06)',
            backdropFilter: 'blur(6px)',
            transition: 'border-color 0.3s',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>

              {/* Left — gesture + stability dots */}
              <div>
                <div style={{
                  fontSize: '10px', color: '#3d6080',
                  fontFamily: "'DM Mono', monospace", marginBottom: '5px', letterSpacing: '0.15em',
                }}>GESTURE</div>
                <div style={{
                  fontSize: prediction ? '22px' : '13px', fontWeight: 800,
                  fontFamily: "'Exo 2', sans-serif",
                  color: prediction ? '#00d4ff' : '#2a4a6a',
                  textShadow: prediction ? '0 0 14px rgba(0,212,255,0.55)' : 'none',
                  transition: 'all 0.2s', letterSpacing: '0.08em',
                }}>
                  {prediction ? prediction.gesture : 'No hand detected'}
                </div>

                {/* Stability dots */}
                {prediction && (
                  <div style={{ display: 'flex', gap: '4px', marginTop: '7px', alignItems: 'center' }}>
                    <span style={{ fontSize: '9px', color: '#3d6080', fontFamily: "'DM Mono', monospace", marginRight: '4px', letterSpacing: '0.1em' }}>
                      LOCK
                    </span>
                    {stabilityDots.map((filled, i) => (
                      <div key={i} style={{
                        width: '8px', height: '8px', borderRadius: '50%',
                        background: filled
                          ? stableCount >= STABILITY_THRESHOLD ? '#10b981' : '#00d4ff'
                          : '#132240',
                        transition: 'background 0.2s',
                        boxShadow: filled ? '0 0 6px rgba(0,212,255,0.5)' : 'none',
                      }} />
                    ))}
                    {stableCount >= STABILITY_THRESHOLD && (
                      <span style={{
                        fontSize: '9px', color: '#10b981', fontFamily: "'DM Mono', monospace",
                        marginLeft: '4px', letterSpacing: '0.1em',
                      }}>✓ ADDED</span>
                    )}
                  </div>
                )}
              </div>

              {/* Right — confidence bar */}
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '10px', color: '#3d6080',
                  fontFamily: "'DM Mono', monospace", marginBottom: '7px', letterSpacing: '0.15em',
                }}>CONFIDENCE</div>
                {prediction ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '80px', height: '5px', borderRadius: '3px', background: '#132240', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: '3px',
                        width: `${pct}%`, background: barColor,
                        transition: 'width 0.4s ease',
                      }} />
                    </div>
                    <span style={{
                      fontSize: '15px', fontWeight: 700, fontFamily: "'DM Mono', monospace",
                      color: pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444',
                    }}>{pct}%</span>
                  </div>
                ) : (
                  <span style={{ fontSize: '13px', color: '#1d3a5a', fontFamily: "'DM Mono', monospace" }}>—</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            position: 'absolute', bottom: '14px', left: '14px', right: '14px', zIndex: 5,
            borderRadius: '10px', padding: '10px 14px', textAlign: 'center',
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)',
            fontSize: '12px', color: '#ef4444',
          }}>⚠ {error}</div>
        )}
      </div>

      {/* ── Camera buttons ───────────────────────────────── */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button onClick={startCamera} disabled={active} style={{
          flex: 1, padding: '11px', borderRadius: '10px',
          fontSize: '13px', fontWeight: 600,
          cursor: active ? 'not-allowed' : 'pointer',
          fontFamily: "'DM Sans', sans-serif",
          background: !active ? 'rgba(16,185,129,0.12)' : '#050c17',
          border: !active ? '1px solid rgba(16,185,129,0.4)' : '1px solid #132240',
          color: !active ? '#10b981' : '#3d6080',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
        }}>📷 Start Camera</button>

        <button onClick={stopCamera} disabled={!active} style={{
          flex: 1, padding: '11px', borderRadius: '10px',
          fontSize: '13px', fontWeight: 600,
          cursor: !active ? 'not-allowed' : 'pointer',
          fontFamily: "'DM Sans', sans-serif",
          background: active ? 'rgba(239,68,68,0.1)' : '#050c17',
          border: active ? '1px solid rgba(239,68,68,0.35)' : '1px solid #132240',
          color: active ? '#ef4444' : '#3d6080',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
        }}>⏹ Stop Camera</button>
      </div>

      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
      `}</style>
    </div>
  );
}