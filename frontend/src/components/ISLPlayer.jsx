import React, {
  useRef, useState, useEffect, useCallback, useMemo
} from 'react';
import videoMap    from './videoMap.js';
import signTimings from './signTimings.js';

// ── Constants ─────────────────────────────────────────────────────────────────
const CROSSFADE_MS      = 250;   // fade duration in ms
const CROSSFADE_LEAD_MS = 200;   // how early before sign ends to start fade

/**
 * ISLPlayer — Double-buffered sequential ISL sign video player.
 *
 * Props:
 *   glosses        : string[]              — ISL gloss tokens to play
 *   onTokenChange  : (idx: number) => void — fires when active sign changes
 */
export default function ISLPlayer({ glosses = [], onTokenChange }) {

  // ── Resolve playable tokens ───────────────────────────────────────────────
  // Filter to only tokens that exist in videoMap; record original gloss index
  const queue = useMemo(() => {
    return glosses
      .map((token, glossIdx) => ({ token, glossIdx, src: videoMap[token] }))
      .filter(item => !!item.src);
  }, [glosses]);

  // ── Refs ──────────────────────────────────────────────────────────────────
  const vidA        = useRef(null);   // buffer A
  const vidB        = useRef(null);   // buffer B
  const crossTimer  = useRef(null);   // timeout for crossfade trigger
  const safetyTimer = useRef(null);   // safety-net timeout

  // ── State ─────────────────────────────────────────────────────────────────
  const [active,     setActive]     = useState(0);    // 0 = A visible, 1 = B visible
  const [queueIdx,   setQueueIdx]   = useState(0);    // current queue position
  const [playing,    setPlaying]    = useState(false);
  const [opacityA,   setOpacityA]   = useState(1);
  const [opacityB,   setOpacityB]   = useState(0);
  const [finished,   setFinished]   = useState(false);

  // ── Helpers ───────────────────────────────────────────────────────────────

  // Return the <video> ref for a buffer index
  const bufRef = useCallback((buf) => buf === 0 ? vidA : vidB, []);

  // Seek a video element to the sign's start time
  const seekToStart = useCallback((el, token) => {
    const timing = signTimings[token];
    el.currentTime = timing ? timing.start : 0;
  }, []);

  // Get the end time for a token (null = play to natural end)
  const getEndTime = useCallback((token) => {
    const timing = signTimings[token];
    return timing ? timing.end : null;
  }, []);

  // Preload a token into a buffer (without playing)
  const preload = useCallback((buf, token, src) => {
    const el = bufRef(buf).current;
    if (!el || !src) return;
    el.src = src;
    el.load();
    seekToStart(el, token);
  }, [bufRef, seekToStart]);

  // ── Launch a sign in a buffer and begin crossfade scheduling ─────────────
  const playBuffer = useCallback((buf, qIdx) => {
    clearTimeout(crossTimer.current);
    clearTimeout(safetyTimer.current);

    const item = queue[qIdx];
    if (!item) return;

    const el      = bufRef(buf).current;
    const endTime = getEndTime(item.token);

    // Seek to start frame
    seekToStart(el, item.token);

    // Play
    el.play().catch(() => {});

    // Notify parent which gloss is now active
    onTokenChange?.(item.glossIdx);

    // If we have a known endTime, schedule crossfade
    if (endTime !== null) {
      const duration = endTime - (signTimings[item.token]?.start ?? 0);
      const delay    = Math.max(0, duration * 1000 - CROSSFADE_LEAD_MS);
      crossTimer.current = setTimeout(() => triggerCrossfade(buf, qIdx), delay);

      // Safety net: if timeupdate-based trigger was missed, fire at endTime + 100ms
      safetyTimer.current = setTimeout(
        () => triggerCrossfade(buf, qIdx),
        duration * 1000 + 100
      );
    }
    // If no endTime, onEnded will trigger the crossfade
  }, [queue, bufRef, getEndTime, seekToStart, onTokenChange]);

  // ── Crossfade: fade out current buffer, fade in next, preload after ───────
  const triggerCrossfade = useCallback((fromBuf, fromQIdx) => {
    clearTimeout(crossTimer.current);
    clearTimeout(safetyTimer.current);

    const nextQIdx = fromQIdx + 1;

    if (nextQIdx >= queue.length) {
      // No more signs — fade out and finish
      if (fromBuf === 0) { setOpacityA(0); } else { setOpacityB(0); }
      setTimeout(() => {
        setPlaying(false);
        setFinished(true);
      }, CROSSFADE_MS);
      return;
    }

    const toBuf     = fromBuf === 0 ? 1 : 0;
    const nextItem  = queue[nextQIdx];
    const nextEl    = bufRef(toBuf).current;

    // Preload next sign into the inactive buffer right now
    nextEl.src = nextItem.src;
    nextEl.load();
    seekToStart(nextEl, nextItem.token);

    // Crossfade: fade out current, fade in next
    if (fromBuf === 0) {
      setOpacityA(0);
      setOpacityB(1);
    } else {
      setOpacityB(0);
      setOpacityA(1);
    }

    // After fade completes: start playing the new buffer
    setTimeout(() => {
      setActive(toBuf);
      setQueueIdx(nextQIdx);
      playBuffer(toBuf, nextQIdx);

      // Preload the one after next into the now-hidden buffer
      const afterNextIdx = nextQIdx + 1;
      if (afterNextIdx < queue.length) {
        const afterItem = queue[afterNextIdx];
        preload(fromBuf, afterItem.token, afterItem.src);
      }
    }, CROSSFADE_MS);
  }, [queue, bufRef, seekToStart, preload, playBuffer]);

  // ── timeupdate handler: watch for endTime on active buffer ───────────────
  const handleTimeUpdate = useCallback((buf) => {
    const item    = queue[queueIdx];
    const endTime = item ? getEndTime(item.token) : null;
    if (endTime === null) return;               // no trimming configured
    if (buf !== active) return;                 // ignore inactive buffer

    const el = bufRef(buf).current;
    if (!el) return;

    const remaining = endTime - el.currentTime;
    if (remaining <= CROSSFADE_LEAD_MS / 1000) {
      triggerCrossfade(buf, queueIdx);
    }
  }, [queue, queueIdx, active, getEndTime, bufRef, triggerCrossfade]);

  // ── onEnded safety net (catches untrimmed or missed crossfade) ────────────
  const handleEnded = useCallback((buf) => {
    if (buf !== active) return;
    triggerCrossfade(buf, queueIdx);
  }, [active, queueIdx, triggerCrossfade]);

  // ── Start playback when queue changes ─────────────────────────────────────
  useEffect(() => {
    if (queue.length === 0) {
      setPlaying(false);
      setFinished(false);
      setQueueIdx(0);
      setActive(0);
      setOpacityA(1);
      setOpacityB(0);
      return;
    }

    // Reset state
    clearTimeout(crossTimer.current);
    clearTimeout(safetyTimer.current);
    setFinished(false);
    setQueueIdx(0);
    setActive(0);
    setOpacityA(1);
    setOpacityB(0);
    setPlaying(true);

    // Load first sign into buffer A
    const first = queue[0];
    const elA   = vidA.current;
    elA.src = first.src;
    elA.load();
    seekToStart(elA, first.token);

    // Preload second sign into buffer B (silent)
    if (queue[1]) {
      preload(1, queue[1].token, queue[1].src);
    }

    // Small tick to let load settle, then play
    const t = setTimeout(() => playBuffer(0, 0), 80);
    return () => clearTimeout(t);
  }, [queue]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Cleanup on unmount ────────────────────────────────────────────────────
  useEffect(() => () => {
    clearTimeout(crossTimer.current);
    clearTimeout(safetyTimer.current);
  }, []);

  // ── Current gloss label for HUD ───────────────────────────────────────────
  const currentToken = queue[queueIdx]?.token ?? '';

  // ── Progress dots (all queue items) ──────────────────────────────────────
  const dots = queue.length > 0 && queue.length <= 12;  // show dots for short sequences

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '10px' }}>

      {/* ── Viewport ──────────────────────────────────────────────────── */}
      <div style={{
        flex: 1, minHeight: '320px', borderRadius: '16px',
        position: 'relative', overflow: 'hidden',
        background: '#020810',
        border: playing
          ? '1px solid rgba(0,212,255,0.5)'
          : finished
          ? '1px solid rgba(16,185,129,0.3)'
          : '1px solid #132240',
        boxShadow: playing ? '0 0 40px rgba(0,212,255,0.08)' : 'none',
        transition: 'border-color 0.4s',
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
            borderColor: playing
              ? 'rgba(0,212,255,0.6)'
              : finished
              ? 'rgba(16,185,129,0.4)'
              : 'rgba(0,212,255,0.2)',
            transition: 'border-color 0.4s',
            ...s,
          }} />
        ))}

        {/* ── Buffer A ──────────────────────────────────────────────── */}
        <video
          ref={vidA}
          playsInline
          muted={false}
          onTimeUpdate={() => handleTimeUpdate(0)}
          onEnded={() => handleEnded(0)}
          style={{
            position: 'absolute', inset: 0,
            width: '100%', height: '100%',
            objectFit: 'contain',
            opacity: opacityA,
            transition: `opacity ${CROSSFADE_MS}ms ease-in-out`,
            zIndex: active === 0 ? 2 : 1,
          }}
        />

        {/* ── Buffer B ──────────────────────────────────────────────── */}
        <video
          ref={vidB}
          playsInline
          muted={false}
          onTimeUpdate={() => handleTimeUpdate(1)}
          onEnded={() => handleEnded(1)}
          style={{
            position: 'absolute', inset: 0,
            width: '100%', height: '100%',
            objectFit: 'contain',
            opacity: opacityB,
            transition: `opacity ${CROSSFADE_MS}ms ease-in-out`,
            zIndex: active === 1 ? 2 : 1,
          }}
        />

        {/* Idle */}
        {!playing && !finished && queue.length === 0 && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 3,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: '14px',
          }}>
            <div style={{ fontSize: '52px', opacity: 0.1 }}>🤟</div>
            <p style={{
              fontSize: '11px', letterSpacing: '0.25em', textTransform: 'uppercase',
              color: '#3d6080', fontFamily: "'DM Mono', monospace",
            }}>Awaiting Input</p>
            <p style={{ fontSize: '11px', color: '#1d3a5a', margin: 0 }}>
              Type a sentence and press Convert
            </p>
          </div>
        )}

        {/* Finished overlay */}
        {finished && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 3,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: '10px',
            background: 'rgba(2,8,16,0.75)', backdropFilter: 'blur(4px)',
          }}>
            <div style={{ fontSize: '32px' }}>✅</div>
            <p style={{
              fontSize: '12px', color: '#10b981', margin: 0,
              fontFamily: "'DM Mono', monospace", letterSpacing: '0.1em',
            }}>Signing complete</p>
          </div>
        )}

        {/* Top-left label */}
        <div style={{
          position: 'absolute', top: '12px', left: '12px', zIndex: 5,
          padding: '3px 8px', borderRadius: '4px',
          background: 'rgba(0,0,0,0.65)', border: '1px solid #132240',
          fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase',
          color: '#3d6080', fontFamily: "'DM Mono', monospace",
        }}>ISL PLAYER</div>

        {/* Current gloss badge — top right */}
        {playing && currentToken && (
          <div style={{
            position: 'absolute', top: '12px', right: '12px', zIndex: 5,
            padding: '5px 14px', borderRadius: '6px',
            background: 'rgba(3,7,13,0.85)',
            border: '1px solid rgba(0,212,255,0.45)',
            fontSize: '15px', fontWeight: 800, letterSpacing: '0.1em',
            color: '#00d4ff', fontFamily: "'Exo 2', sans-serif",
            textShadow: '0 0 12px rgba(0,212,255,0.5)',
            transition: 'opacity 0.2s',
          }}>
            {currentToken}
          </div>
        )}

        {/* Progress dots — bottom centre */}
        {dots && queue.length > 0 && (
          <div style={{
            position: 'absolute', bottom: '14px', left: 0, right: 0,
            display: 'flex', justifyContent: 'center',
            gap: '6px', zIndex: 5,
          }}>
            {queue.map((item, i) => {
              const done    = i < queueIdx;
              const current = i === queueIdx && playing;
              return (
                <div key={i} title={item.token} style={{
                  height: '6px',
                  width: current ? '20px' : '6px',
                  borderRadius: '3px',
                  background: current
                    ? '#00d4ff'
                    : done
                    ? 'rgba(0,212,255,0.35)'
                    : '#132240',
                  boxShadow: current ? '0 0 8px rgba(0,212,255,0.7)' : 'none',
                  transition: 'all 0.3s ease',
                }} />
              );
            })}
          </div>
        )}


      </div>
    </div>
  );
}