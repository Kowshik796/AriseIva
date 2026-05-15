"""
arise-iva | Model Repair & Training Script
==========================================
Diagnoses corrupt / missing pkl files, then rebuilds them from the CSV.
Run this instead of train_model.py if you get 'invalid load key' errors.

Usage
-----
    cd arise-iva
    python scripts/repair_models.py
"""

from __future__ import annotations
import os, sys, pickle
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)

DATASET_CSV  = os.path.join(_PROJECT_DIR, "dataset", "processed_landmarks", "gesture_dataset.csv")
MODELS_DIR   = os.path.join(_PROJECT_DIR, "dataset", "trained_models")
MODEL_PKL    = os.path.join(MODELS_DIR, "gesture_model.pkl")
LABELS_PKL   = os.path.join(MODELS_DIR, "label_classes.pkl")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _diagnose(path: str, name: str) -> None:
    """Print size + first 8 bytes of a file so we can see corruption."""
    if not os.path.exists(path):
        print(f"  [{name}]  MISSING — {path}")
        return
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(8)
    ok = head[:2] == b'\x80\x05' or head[:2] == b'\x80\x04' or head[:2] == b'\x80\x02'
    status = "OK" if ok else "CORRUPT"
    print(f"  [{name}]  {status}  size={size}B  first_bytes={head}  path={path}")


def _delete_if_exists(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
        print(f"  Deleted corrupt file: {path}")


def _save_binary(obj, path: str) -> None:
    """Always write in binary mode — the only correct way for pickle."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f, protocol=4)
    # Verify immediately
    with open(path, "rb") as f:
        head = f.read(2)
    assert head == b'\x80\x04', f"Write verification failed — first bytes: {head}"
    print(f"  Saved (verified): {path}")


def _train_from_csv() -> tuple:
    """Load CSV and train. Returns (model, labels_array)."""
    try:
        import pandas as pd
    except ImportError:
        print("\n  [ERROR] pandas not installed.")
        print("  Run:  pip install pandas scikit-learn")
        sys.exit(1)

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
    except ImportError:
        print("\n  [ERROR] scikit-learn not installed.")
        print("  Run:  pip install scikit-learn")
        sys.exit(1)

    if not os.path.exists(DATASET_CSV):
        print(f"\n  [ERROR] Dataset CSV not found: {DATASET_CSV}")
        print("  Run scripts/collect_data.py first to collect gesture samples.")
        sys.exit(1)

    df = pd.read_csv(DATASET_CSV)
    print(f"\n  Loaded {len(df)} rows from CSV.")
    print(f"  Gestures: {sorted(df['label'].unique().tolist())}\n")

    if len(df) < 10:
        print("  [ERROR] Too few samples. Collect at least 10 rows per gesture.")
        sys.exit(1)

    labels      = sorted(df["label"].unique().tolist())
    label_to_id = {lbl: i for i, lbl in enumerate(labels)}
    X = df.drop(columns=["label"]).values.astype(np.float32)
    y = df["label"].map(label_to_id).values.astype(np.int32)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    print("  Training RandomForestClassifier …")
    clf.fit(X_tr, y_tr)

    acc = accuracy_score(y_te, clf.predict(X_te))
    print(f"  Test accuracy: {acc*100:.2f} %")

    return clf, np.array(labels, dtype=str)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 54)
    print("   Arise IVA  —  Model Repair & Training")
    print("=" * 54)

    print("\n[ Diagnosis ]")
    _diagnose(MODEL_PKL,  "gesture_model.pkl")
    _diagnose(LABELS_PKL, "label_classes.pkl")

    print("\n[ Removing corrupt/old files ]")
    _delete_if_exists(MODEL_PKL)
    _delete_if_exists(LABELS_PKL)

    print("\n[ Training from CSV ]")
    model, labels = _train_from_csv()

    print("\n[ Saving binary pkl files ]")
    _save_binary(model,  MODEL_PKL)
    _save_binary(labels, LABELS_PKL)

    print("\n[ Final verification — loading back ]")
    with open(MODEL_PKL,  "rb") as f: m = pickle.load(f)
    with open(LABELS_PKL, "rb") as f: l = pickle.load(f)
    print(f"  Model type   : {type(m).__name__}")
    print(f"  Labels loaded: {l.tolist()}")

    print("\n  ✓ All files verified. Run  python app/main.py  now.\n")


if __name__ == "__main__":
    main()