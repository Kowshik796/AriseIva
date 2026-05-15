import React, { useState, useRef, useEffect } from 'react';

export default function SpeechInput({ onConvert, loading }) {
  const [text, setText] = useState('');
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    setSpeechSupported(!!SR);
    if (SR) {
      const r = new SR();
      r.continuous = false;
      r.interimResults = true;
      r.lang = 'en-IN';
      r.onresult = (e) => {
        const t = Array.from(e.results).map(x => x[0].transcript).join('');
        setText(t);
      };
      r.onend = () => setListening(false);
      recognitionRef.current = r;
    }
  }, []);

  const toggleListen = () => {
    if (!recognitionRef.current) return;
    if (listening) {
      recognitionRef.current.stop();
    } else {
      setText('');
      recognitionRef.current.start();
      setListening(true);
    }
  };

  const btn = (label, onClick, disabled, accent) => ({
    padding: '10px 16px', borderRadius: '10px', fontSize: '13px',
    fontFamily: "'DM Sans', sans-serif", fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s',
    border: `1px solid ${disabled ? '#132240' : accent + '66'}`,
    background: disabled ? '#050c17' : `${accent}18`,
    color: disabled ? '#3d6080' : accent,
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

      {/* Mic button */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
        <button onClick={toggleListen} disabled={!speechSupported} style={{
          width: '64px', height: '64px', borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: speechSupported ? 'pointer' : 'not-allowed', fontSize: '24px',
          background: listening
            ? 'linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,212,255,0.08))'
            : 'linear-gradient(135deg, #0d1e36, #0a1628)',
          border: listening ? '2px solid #00d4ff' : '2px solid #132240',
          boxShadow: listening ? '0 0 24px rgba(0,212,255,0.4)' : 'none',
          transition: 'all 0.3s',
        }}>
          {listening ? '🔴' : '🎙️'}
        </button>
        <span style={{
          fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase',
          color: listening ? '#00d4ff' : '#3d6080', fontFamily: "'DM Mono', monospace",
        }}>
          {!speechSupported ? 'Mic Unavailable' : listening ? '● Recording...' : 'Start Listening'}
        </span>
      </div>

      {/* Divider */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ flex: 1, height: '1px', background: '#132240' }} />
        <span style={{ fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#3d6080', fontFamily: "'DM Mono', monospace" }}>
          or type
        </span>
        <div style={{ flex: 1, height: '1px', background: '#132240' }} />
      </div>

      {/* Textarea */}
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Type or speak a sentence..."
        rows={4}
        style={{
          width: '100%', resize: 'none', borderRadius: '10px',
          padding: '14px', fontSize: '14px', lineHeight: '1.6',
          outline: 'none', boxSizing: 'border-box',
          background: '#050c17',
          border: text ? '1px solid rgba(0,212,255,0.3)' : '1px solid #132240',
          color: '#d6eeff', fontFamily: "'DM Sans', sans-serif",
          caretColor: '#00d4ff',
        }}
      />

      {/* Buttons */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => text.trim() && onConvert(text.trim())}
          disabled={!text.trim() || loading}
          style={{ ...btn('Convert', null, !text.trim() || loading, '#00d4ff'), flex: 1 }}>
          {loading ? '⏳ Converting...' : '→ Convert to ISL'}
        </button>
        <button
          onClick={() => setText('')}
          style={{
            width: '46px', height: '46px', borderRadius: '10px', fontSize: '16px',
            cursor: 'pointer', border: '1px solid #132240',
            background: '#050c17', color: '#3d6080', flexShrink: 0,
          }}>
          🗑
        </button>
      </div>
    </div>
  );
}