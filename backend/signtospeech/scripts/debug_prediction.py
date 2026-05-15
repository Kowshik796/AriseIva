"""
Run this FIRST. It will tell us exactly what is broken.
    cd arise-iva
    python scripts/debug_prediction.py
"""
import sys, pickle, os
from pathlib import Path
import numpy as np

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_DIR / "app"))

MODEL_PKL  = _PROJECT_DIR / "dataset" / "trained_models" / "gesture_model.pkl"
LABELS_PKL = _PROJECT_DIR / "dataset" / "trained_models" / "label_classes.pkl"
CSV_PATH   = _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

print("\n" + "="*60)
print("  ARISE IVA — FULL PREDICTION DEBUG")
print("="*60)

# ── 1. Load model ──────────────────────────────────────────────────────────────
with open(MODEL_PKL,  "rb") as f: model  = pickle.load(f)
with open(LABELS_PKL, "rb") as f: labels = pickle.load(f)
labels = [str(l) for l in labels]

n_feat = model.n_features_in_ if hasattr(model, "n_features_in_") else len(model.feature_importances_)

print(f"\n[MODEL]")
print(f"  Type            : {type(model).__name__}")
print(f"  n_features_in_  : {n_feat}")
print(f"  label_classes   : {labels}")

# Check if model has its own classes_ (CRITICAL for LightGBM)
if hasattr(model, "classes_"):
    model_classes = [str(c) for c in model.classes_]
    print(f"  model.classes_  : {model_classes}")
    if model_classes != labels:
        print(f"\n  *** MISMATCH *** model.classes_ != label_classes.pkl")
        print(f"  This is why predictions are wrong!")
        print(f"  USING model.classes_ as ground truth")
        labels = model_classes
    else:
        print(f"  classes_ match label_classes.pkl ✓")

# ── 2. Grab a real row from CSV and predict it ─────────────────────────────────
print(f"\n[CSV SANITY CHECK]")
rows_by_label = {}
with open(CSV_PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i == 0: continue
        parts = line.strip().split(",")
        if len(parts) != n_feat + 1: continue
        lbl = parts[0].strip().upper()
        if lbl not in rows_by_label:
            rows_by_label[lbl] = [float(v) for v in parts[1:]]

print(f"  Labels in CSV   : {sorted(rows_by_label.keys())}")
print(f"\n  Predicting one real row per label:")
print(f"  {'Label':<20} {'Predicted':<20} {'Confidence':>10}  Match?")
print(f"  {'-'*20} {'-'*20} {'-'*10}  {'-----'}")

all_correct = 0
for true_label, feats in sorted(rows_by_label.items()):
    x = np.array(feats, dtype=np.float32).reshape(1, -1)
    if hasattr(model, "predict_proba"):
        proba     = model.predict_proba(x)[0]
        class_idx = int(np.argmax(proba))
        conf      = float(proba[class_idx])
        if hasattr(model, "classes_"):
            pred = str(model.classes_[class_idx])
        else:
            pred = labels[class_idx] if class_idx < len(labels) else f"IDX_{class_idx}"
    else:
        pred = str(model.predict(x)[0])
        conf = 1.0

    match = "✓" if pred == true_label else "✗"
    if pred == true_label: all_correct += 1
    print(f"  {true_label:<20} {pred:<20} {conf:>10.1%}  {match}")

print(f"\n  Result: {all_correct}/{len(rows_by_label)} correct on CSV rows")
if all_correct == len(rows_by_label):
    print("  Model predicts CSV data perfectly — problem is in live extraction")
elif all_correct == 0:
    print("  Model predicts NOTHING correctly — model/label mismatch or bad training data")
else:
    print("  Partial match — some labels are confused")

# ── 3. Check live extractor vector ────────────────────────────────────────────
print(f"\n[LIVE EXTRACTOR]")
print(f"  Model needs     : {n_feat} features")
print(f"  42 = single-hand, 84 = dual-hand")
from vision.landmark_processor import LandmarkProcessor
proc = LandmarkProcessor()
print(f"  extract_landmarks()      → 42 features (single-hand)")
print(f"  extract_dual_landmarks() → 84 features (dual-hand)")

if n_feat == 42:
    print(f"\n  main.py MUST call: processor.extract_landmarks(results)")
elif n_feat == 84:
    print(f"\n  main.py MUST call: processor.extract_dual_landmarks(results)")

print("\n" + "="*60 + "\n")