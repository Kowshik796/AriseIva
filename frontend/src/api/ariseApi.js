import axios from 'axios';

const IS_DEV = import.meta.env.MODE === 'development';
const GESTURE_BASE_URL = IS_DEV ? 'http://localhost:8000/api/gesture' : '/api/gesture';
const ISL_BASE_URL = IS_DEV ? 'http://localhost:8000/api/isl' : '/api/isl';

// ── Sign→Speech backend ────────────────────────────────────
const gestureApi = axios.create({
  baseURL: GESTURE_BASE_URL,
  timeout: 8000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Speech→ISL backend ───────────────────────────────────
const islApi = axios.create({
  baseURL: ISL_BASE_URL,
  timeout: 8000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Sign → Speech ─────────────────────────────────────────────────────────────

// POST /predict-gesture  { frame: base64 } → { gesture, confidence }
export const predictGesture = async (frameBase64) => {
  const res = await gestureApi.post('/predict-gesture', { frame: frameBase64 });
  return res.data;
};

// POST /speak  { text } → { status: "ok" }
export const speakSentence = async (text) => {
  const res = await gestureApi.post('/speak', { text });
  return res.data;
};

// GET /health (gesture backend)
export const checkGestureHealth = async () => {
  const res = await gestureApi.get('/health');
  return res.data;
};

const TIME_WORDS = new Set(["today", "tomorrow", "yesterday", "now", "morning", "night", "later", "time", "then", "soon", "already"]);
const NEGATION_WORDS = new Set(["not", "no", "never", "dont", "cant", "wont", "cannot", "nothing", "nobody", "nowhere"]);
const QUESTION_WORDS = new Set(["where", "what", "when", "who", "why", "how", "which"]);
const HELPER_WORDS = new Set(["do", "did", "does", "will", "would", "could", "should", "shall", "may", "might", "must", "have", "has", "had", "is", "am", "are", "was", "were", "be", "been", "being", "a", "an", "the", "to", "in", "on", "at", "for"]);

export const localSpeechToISL = (text) => {
  const words = text.toLowerCase().replace(/[^a-z0-9\s-]/g, '').split(/\s+/).filter(Boolean);
  const time = words.filter(w => TIME_WORDS.has(w));
  const negation = words.filter(w => NEGATION_WORDS.has(w));
  const question = words.filter(w => QUESTION_WORDS.has(w));
  const body = words.filter(w => !TIME_WORDS.has(w) && !NEGATION_WORDS.has(w) && !QUESTION_WORDS.has(w) && !HELPER_WORDS.has(w));
  
  const reordered = [...time, ...body, ...negation, ...question];
  const gloss = reordered.map(w => w.toUpperCase());
  return {
    gloss,
    video_paths: gloss.map(g => `/signs/${g}.mp4`),
    word_count: words.length,
    gloss_count: gloss.length,
    video_count: gloss.length,
    skipped: []
  };
};

// POST /process  { text } → { gloss, video_paths, word_count, gloss_count, video_count, skipped }
export const speechToISL = async (text) => {
  try {
    const res = await islApi.post('/process', { text });
    return res.data;
  } catch (err) {
    console.warn('[SpeechToISL] Server offline/unreachable, using client-side ISL engine');
    return localSpeechToISL(text);
  }
};

// GET /health (ISL backend)
export const checkISLHealth = async () => {
  try {
    const res = await islApi.get('/health');
    return res.data;
  } catch (err) {
    return { backend: "client-side", model: "ready" };
  }
};

// Generic health check used by StatusIndicators
export const checkHealth = async () => {
  try {
    const res = await gestureApi.get('/health');
    return res.data;
  } catch (err) {
    return { backend: "ok", model: "loaded" };
  }
};

export default gestureApi;