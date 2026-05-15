import React, { useEffect, useState } from 'react';
import { checkHealth } from '../api/ariseApi.js';

function Indicator({ label, status }) {
  // status: 'active' | 'inactive' | 'loading'
  const color =
    status === 'active'  ? '#10b981' :
    status === 'loading' ? '#f59e0b' : '#ef4444';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ position: 'relative', width: '8px', height: '8px', flexShrink: 0 }}>
        <div style={{
          width: '8px', height: '8px', borderRadius: '50%', background: color,
        }} />
        {status === 'active' && (
          <div style={{
            position: 'absolute', inset: '-3px', borderRadius: '50%',
            border: `1px solid ${color}`,
            animation: 'ripple 1.5s ease-out infinite',
            opacity: 0,
          }} />
        )}
      </div>
      <span style={{
        fontSize: '11px', letterSpacing: '0.05em',
        color: status === 'active' ? '#7aa2c0' : '#4a6080',
        fontFamily: "'DM Mono', monospace",
      }}>
        {label}
      </span>
    </div>
  );
}

export default function StatusIndicators({ cameraActive }) {
  const [backendOk, setBackendOk] = useState(null);  // null=loading
  const [modelOk,   setModelOk]   = useState(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const data = await checkHealth();
        setBackendOk(data.backend === 'ok');
        setModelOk(data.model === 'loaded');
      } catch {
        setBackendOk(false);
        setModelOk(false);
      }
    };
    poll();
    const id = setInterval(poll, 8000);
    return () => clearInterval(id);
  }, []);

  const toStatus = (val) =>
    val === null ? 'loading' : val ? 'active' : 'inactive';

  return (
    <div style={{
      padding: '14px 16px', borderRadius: '12px',
      background: '#050c17', border: '1px solid #132240',
      display: 'flex', flexDirection: 'column', gap: '10px',
    }}>
      <p style={{
        fontSize: '10px', letterSpacing: '0.25em', textTransform: 'uppercase',
        color: '#3d6080', fontFamily: "'DM Mono', monospace", margin: '0 0 4px 0',
      }}>
        System Status
      </p>
      <Indicator label="Backend"       status={toStatus(backendOk)} />
      <Indicator label="Gesture Model" status={toStatus(modelOk)}   />
      <Indicator label="Camera"        status={cameraActive ? 'active' : 'inactive'} />

      <style>{`
        @keyframes ripple {
          0%   { opacity: 0.6; transform: scale(1); }
          100% { opacity: 0;   transform: scale(2.5); }
        }
      `}</style>
    </div>
  );
}