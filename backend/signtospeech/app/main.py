"""
arise-iva | main.py — Flask API Server
=======================================
Converts the standalone OpenCV app into a REST API for the React frontend.

Endpoints:
  GET  /health            → { "backend": "ok", "model": "loaded" }
  POST /predict-gesture   → { "gesture": "HELLO", "confidence": 0.92 }
  POST /speak             → { "status": "ok" }
"""

from __future__ import annotations

import base64
import sys
import numpy as np
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# ── App setup (MUST come before CORS) ────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])

# ── Paths ─────────────────────────────────────────────────────────────────────
_APP_DIR     = Path(__file__).resolve().parent
_PROJECT_DIR = _APP_DIR.parent
MODEL_PATH   = str(_PROJECT_DIR / "dataset" / "trained_models" / "gesture_model.pkl")
LABELS_PATH  = str(_PROJECT_DIR / "dataset" / "trained_models" / "label_classes.pkl")

# ── Import your existing modules ──────────────────────────────────────────────
from vision.hand_detector      import HandDetector
from vision.landmark_processor import LandmarkProcessor
from model.model_loader        import ModelLoader
from model.predictor           import GesturePredictor
from speech.text_to_speech     import TextToSpeech

# ── Load model once at startup ────────────────────────────────────────────────
print("[Server] Loading gesture model...")
try:
    model, scaler, labels, n_features = ModelLoader(MODEL_PATH, LABELS_PATH).load()
    use_dual  = (n_features == 84)
    mode_str  = f"{'DUAL' if use_dual else 'SINGLE'}-HAND | {n_features}f"
    MODEL_OK  = True
    print(f"[Server] Model loaded — {mode_str}")
except Exception as e:
    MODEL_OK = False
    model = scaler = labels = n_features = None
    use_dual = False
    print(f"[Server] WARNING — model failed to load: {e}")

# ── Init pipeline (shared across requests) ────────────────────────────────────
detector  = HandDetector(max_hands=2 if use_dual else 1, detection_confidence=0.6)
processor = LandmarkProcessor()
predictor = GesturePredictor(model, scaler, labels) if MODEL_OK else None
tts       = TextToSpeech(rate=145, volume=1.0)


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    """Frontend polls this to check if backend + model are ready."""
    return jsonify({
        "backend": "ok",
        "model":   "loaded" if MODEL_OK else "not loaded",
    })


@app.route("/predict-gesture", methods=["POST"])
def predict_gesture():
    """
    Receives a base64 JPEG frame from the React webcam,
    runs your gesture model, returns gesture + confidence.
    """
    if not MODEL_OK:
        return jsonify({"error": "Model not loaded"}), 503

    data = request.get_json(silent=True)
    if not data or "frame" not in data:
        return jsonify({"error": "Missing 'frame' field"}), 400

    # ── Decode base64 → OpenCV frame ─────────────────────────────────────────
    try:
        img_bytes = base64.b64decode(data["frame"])
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        import cv2
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("cv2.imdecode returned None")
    except Exception as e:
        return jsonify({"error": f"Invalid frame: {e}"}), 400

    # ── Run hand detection ────────────────────────────────────────────────────
    try:
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = detector.hands.process(rgb)

        # Extract feature vector (single or dual hand)
        vector = (
            processor.extract_dual_landmarks(results)
            if use_dual
            else processor.extract_landmarks(results)
        )

        if vector is None:
            # No hand visible in frame
            return jsonify({"gesture": None, "confidence": 0.0})

        # ── Predict ───────────────────────────────────────────────────────────
        gesture, confidence = predictor.predict(vector)

        if gesture == "Unknown" or confidence < 0.40:
            return jsonify({"gesture": None, "confidence": round(float(confidence), 4)})

        return jsonify({
            "gesture":    gesture,
            "confidence": round(float(confidence), 4),
        })

    except Exception as e:
        print(f"[predict-gesture] Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/speak", methods=["POST"])
def speak():
    """
    Receives a sentence string from the frontend,
    speaks it using your existing TextToSpeech module.
    """
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    try:
        # Capitalise each word for natural speech (matches original app behaviour)
        spoken = " ".join(w.capitalize() for w in text.split())
        tts.speak(spoken)
        print(f"[speak] Speaking: '{spoken}'")
        return jsonify({"status": "ok", "spoken": spoken})
    except Exception as e:
        print(f"[speak] Error: {e}")
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("[Server] Starting Arise IVA API on http://0.0.0.0:5000")
    print("[Server] Endpoints: GET /health  POST /predict-gesture  POST /speak")
    app.run(host="0.0.0.0", port=5000, debug=False)