import React, { useState, useEffect, useRef } from 'react';
import { speakSentence } from '../api/ariseApi.js';

// ── Tuning constants ──────────────────────────────────────────────────────────
const SAME_GESTURE_COOLDOWN_MS = 2500;  // must wait this long before same word added again
const MIN_CONFIDENCE           = 0.70;  // ignore anything below this

export default function SentenceBuilder({ detectedGesture }) {
  const [words,    setWords]    = useState([]);
  const [speaking, setSpeaking] = useState(false);
  const [status,   setStatus]   = useState('');

  // Track last added word + timestamp
  const lastRef = useRef({ gesture: '', time: 0 });

  useEffect(() => {
    if (!detectedGesture) return;
    const { gesture, confidence } = detectedGesture;

    // ── Gate 1: confidence threshold ─────────────────────────────────────────
    if (confidence < MIN_CONFIDENCE) return;

    const now  = Date.now();
    const last = lastRef.current;

    // ── Gate 2: same word cooldown ────────────────────────────────────────────
    // If the SAME gesture fires again before cooldown expires → ignore
    if (gesture === last.gesture && now - last.time < SAME_GESTURE_COOLDOWN_MS) return;

    // ── Gate 3: don't add the same word twice in a row (ever) ────────────────
    setWords(prev => {
      if (prev.length > 0 && prev[prev.length - 1] === gesture) return prev;
      return [...prev, gesture];
    });

    lastRef.current = { gesture, time: now };
    setStatus('');
  }, [detectedGesture]);

  const sentence = words.join(' ');

  const handleSpeak = async () => {
    if (!sentence || speaking) return;
    setSpeaking(true);
    setStatus('');
    try {
      await speakSentence(sentence);
      setStatus('✓ Sent to backend TTS');
    } catch {
      if (window.speechSynthesis) {
        const utt = new SpeechSynthesisUtterance(sentence);
        utt.lang = 'en-IN';
        utt.rate = 0.95;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utt);
        setStatus('✓ Speaking via browser TTS');
      } else {
        setStatus('⚠ Speech unavailable');
      }
    } finally {
      setSpeaking(false);
    }
  };

  const handleClear = () => {
    setWords([]);
    setStatus('');
    lastRef.current = { gesture: '', time: 0 };
    window.speechSynthesis?.cancel();
  };

  const removeWord = (idx) =>
    setWords(prev => prev.filter((_, i) => i !== idx));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{
        borderRadius: '12px', padding: '16px',
        background: '#050c17', border: '1px solid #132240',
      }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <p style={{
            fontSize: '10px', letterSpacing: '0.25em', textTransform: 'uppercase',
            color: '#3d6080', fontFamily: "'DM Mono', monospace", margin: 0,
          }}>Sentence Builder</p>
          <span style={{ fontSize: '10px', color: '#3d6080', fontFamily: "'DM Mono', monospace" }}>
            {words.length} word{words.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Word chips */}
        <div style={{
          minHeight: '56px', display: 'flex', flexWrap: 'wrap', gap: '7px',
          padding: '10px', borderRadius: '8px', marginBottom: '12px',
          background: '#040b14', border: '1px solid #0a1628', alignContent: 'flex-start',
        }}>
          {words.length === 0 ? (
            <span style={{
              fontSize: '12px', color: '#1d3a5a',
              fontFamily: "'DM Mono', monospace", alignSelf: 'center', margin: 'auto',
            }}>
              Detected signs will appear here…
            </span>
          ) : (
            words.map((word, i) => (
              <span key={i} onClick={() => removeWord(i)} title="Click to remove"
                style={{
                  padding: '5px 11px', borderRadius: '7px', fontSize: '12px',
                  fontWeight: 700, letterSpacing: '0.06em', cursor: 'pointer',
                  userSelect: 'none',
                  background: 'rgba(0,212,255,0.1)',
                  border: '1px solid rgba(0,212,255,0.25)',
                  color: '#00d4ff', fontFamily: "'Exo 2', sans-serif",
                }}>
                {word} <span style={{ fontSize: '9px', opacity: 0.45 }}>✕</span>
              </span>
            ))
          )}
        </div>

        {/* Sentence preview */}
        {sentence && (
          <div style={{
            padding: '10px 14px', borderRadius: '8px', marginBottom: '12px',
            background: 'rgba(124,58,237,0.07)', border: '1px solid rgba(124,58,237,0.18)',
            fontSize: '13px', fontStyle: 'italic', color: '#c4a8ff', lineHeight: 1.5,
          }}>
            › "{sentence}"
          </div>
        )}

        {/* Buttons */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={handleSpeak} disabled={!sentence || speaking} style={{
            flex: 1, padding: '11px', borderRadius: '10px',
            fontSize: '13px', fontWeight: 600,
            cursor: sentence && !speaking ? 'pointer' : 'not-allowed',
            fontFamily: "'DM Sans', sans-serif",
            background: sentence && !speaking ? 'rgba(124,58,237,0.16)' : '#050c17',
            border: sentence && !speaking ? '1px solid rgba(124,58,237,0.45)' : '1px solid #132240',
            color: sentence && !speaking ? '#c4a8ff' : '#3d6080',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            boxShadow: sentence && !speaking ? '0 0 18px rgba(124,58,237,0.12)' : 'none',
          }}>
            {speaking ? '⏳ Speaking…' : '🔊 Speak Sentence'}
          </button>
          <button onClick={handleClear} disabled={words.length === 0} style={{
            width: '46px', height: '46px', borderRadius: '10px', fontSize: '16px',
            cursor: words.length > 0 ? 'pointer' : 'not-allowed', flexShrink: 0,
            background: '#050c17', border: '1px solid #132240', color: '#3d6080',
          }}>🗑</button>
        </div>

        {/* Status */}
        {status && (
          <p style={{
            marginTop: '10px', fontSize: '11px', textAlign: 'center',
            color: status.startsWith('✓') ? '#10b981' : '#f59e0b',
            fontFamily: "'DM Mono', monospace",
          }}>{status}</p>
        )}
      </div>
    </div>
  );
}