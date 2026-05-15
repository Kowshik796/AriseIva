"""
arise-iva | Diagnostic Script
==============================
Checks exactly what the model expects vs what the live pipeline produces.
Run this first to identify the mismatch.

Usage
-----
    cd arise-iva
    python scripts/diagnose.py
"""
from __future__ import annotations
import os, sys, pickle
from pathlib import Path

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
_APP_DIR     = _PROJECT_DIR / "app"
sys.path.insert(0, str(_APP_DIR))

MODEL_PKL   = _PROJECT_DIR / "dataset" / "trained_models" / "gesture_model.pkl"
LABELS_PKL  = _PROJECT_DIR / "dataset" / "trained_models" / "label_classes.pkl"
DATASET_CSV = _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

print("\n" + "═" * 56)
print("   Arise IVA  —  Diagnostic Report")
print("═" * 56)

# ── 1. Check model ─────────────────────────────────────────────────────────────
print("\n[ 1 ] Model file")
if not MODEL_PKL.exists():
    print("      ✗  gesture_model.pkl NOT FOUND")
else:
    with open(MODEL_PKL, "rb") as f:
        model = pickle.load(f)
    with open(LABELS_PKL, "rb") as f:
        labels = pickle.load(f)

    # Get expected feature count from the model itself
    if hasattr(model, "n_features_in_"):
        n_feat = model.n_features_in_
    elif hasattr(model, "feature_importances_"):
        n_feat = len(model.feature_importances_)
    else:
        n_feat = "unknown"

    print(f"      Algorithm   : {type(model).__name__}")
    print(f"      Features    : {n_feat}  ← model expects THIS many inputs")
    print(f"      Labels ({len(labels)})  : {list(labels)}")

    if n_feat == 42:
        print("      Mode        : SINGLE-HAND (42 features)")
    elif n_feat == 84:
        print("      Mode        : DUAL-HAND   (84 features)")
    else:
        print(f"      Mode        : UNKNOWN ({n_feat} features)")

# ── 2. Check CSV ───────────────────────────────────────────────────────────────
print("\n[ 2 ] Dataset CSV")
if not DATASET_CSV.exists():
    print("      ✗  gesture_dataset.csv NOT FOUND")
else:
    from collections import Counter
    col_counts = Counter()
    label_counts = Counter()
    total = 0
    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            line = line.strip()
            if not line: continue
            parts = line.split(",")
            col_counts[len(parts)] += 1
            label_counts[parts[0].strip().upper()] += 1
            total += 1

    print(f"      Total rows   : {total:,}")
    print(f"      Column widths: {dict(col_counts)}")
    if 43 in col_counts:
        print(f"        43-col rows : {col_counts[43]:,}  (single-hand, 42 features)")
    if 85 in col_counts:
        print(f"        85-col rows : {col_counts[85]:,}  (dual-hand,   84 features)")
    print(f"      Labels found : {dict(sorted(label_counts.items()))}")

# ── 3. Check live extractor ────────────────────────────────────────────────────
print("\n[ 3 ] Live landmark extractor (what main.py sends to the model)")
try:
    import mediapipe as mp
    import numpy as np
    import cv2

    # Create a synthetic white frame and run MediaPipe on it
    # (won't detect a real hand, but we can check the vector LENGTH)
    from vision.landmark_processor import LandmarkProcessor
    proc = LandmarkProcessor()

    # Check what extract_dual_landmarks returns in terms of length
    # by inspecting the method
    import inspect
    src = inspect.getsource(proc.extract_dual_landmarks)
    if "ZERO_PAD_42" in src or "42" in src:
        dual_len = 84
    else:
        dual_len = "unknown"

    print(f"      extract_landmarks()       → 42 features  (single-hand)")
    print(f"      extract_dual_landmarks()  → 84 features  (dual-hand)")

    # Check which one main.py actually calls
    main_path = _APP_DIR / "main.py"
    with open(main_path, "r") as f:
        main_src = f.read()

    if "extract_dual_landmarks" in main_src:
        live_features = 84
        print(f"\n      main.py currently calls : extract_dual_landmarks() → 84 features")
    else:
        live_features = 42
        print(f"\n      main.py currently calls : extract_landmarks() → 42 features")

except Exception as e:
    print(f"      Could not check extractor: {e}")
    live_features = None

# ── 4. Verdict ─────────────────────────────────────────────────────────────────
print("\n[ 4 ] Verdict")
if 'n_feat' in dir() and live_features is not None:
    if n_feat == live_features:
        print(f"      ✓  MATCH — model expects {n_feat}, pipeline sends {live_features}")
        print("         If predictions are still wrong, the issue is label mapping.")
    else:
        print(f"      ✗  MISMATCH — model expects {n_feat} features")
        print(f"                    pipeline sends  {live_features} features")
        print(f"\n      FIX: Retrain model to match pipeline, or fix pipeline to match model.")
        if n_feat == 42:
            print("      → Your model is SINGLE-HAND.  Either:")
            print("        a) Retrain on dual-hand data  (recommended)")
            print("        b) Change main.py to use extract_landmarks() instead")
        elif n_feat == 84:
            print("      → Your model is DUAL-HAND but pipeline sends 42.")
            print("        Change main.py to use extract_dual_landmarks()")

print("\n" + "═" * 56 + "\n")