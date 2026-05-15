import axios from 'axios';

// ── Sign→Speech backend (Flask, port 5000) ────────────────────────────────────
const gestureApi = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 8000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Speech→ISL backend (FastAPI, port 8000) ───────────────────────────────────
const islApi = axios.create({
  baseURL: 'http://localhost:8000',
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

// ── Speech → ISL ──────────────────────────────────────────────────────────────

// POST /process  { text } → { gloss, video_paths, word_count, gloss_count, video_count, skipped }
export const speechToISL = async (text) => {
  const res = await islApi.post('/process', { text });
  return res.data;
};

// GET /health (ISL backend)
export const checkISLHealth = async () => {
  const res = await islApi.get('/health');
  return res.data;
};

// Generic health check used by StatusIndicators
export const checkHealth = async () => {
  const res = await gestureApi.get('/health');
  return res.data;
};

export default gestureApi;