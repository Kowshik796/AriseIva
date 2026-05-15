"""
arise-iva | train_model.py — Unified Single + Dual Hand Model
=============================================================
One model, 84 features, handles both sign types:

  Single-hand sign  →  [left_42  +  0,0,0...0,0,0]  = 84 features
  Dual-hand sign    →  [left_42  +  right_42      ]  = 84 features

Run clean_csv.py FIRST — it pads all 43-col rows to 85-col.
Then run this script to train on the unified dataset.

Usage
-----
    python scripts/train_model.py
    python scripts/train_model.py --fast
    python scripts/train_model.py --csv path\\to\\file.csv
    python scripts/train_model.py --csv path\\to\\file.csv --fast
"""
from __future__ import annotations
import sys, pickle, time
from collections import Counter
from pathlib import Path
import numpy as np

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent

_csv_arg = next((sys.argv[i+1] for i, a in enumerate(sys.argv)
                 if a == "--csv" and i+1 < len(sys.argv)), None)
DATASET_PATH = Path(_csv_arg) if _csv_arg else \
               _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

MODELS_DIR  = _PROJECT_DIR / "dataset" / "trained_models"
MODEL_PKL   = MODELS_DIR / "gesture_model.pkl"
LABELS_PKL  = MODELS_DIR / "label_classes.pkl"
REPORT_PATH = MODELS_DIR / "training_report.txt"

DUAL_COLS   = 85   # label + 84 features  (unified target)
SINGLE_COLS = 43   # label + 42 features  (auto-padded to 84)


# ══════════════════════════════════════════════════════════════════════════════
# CSV loader — accepts 85-col (dual) and 43-col (single, auto-padded)
# ══════════════════════════════════════════════════════════════════════════════

def load_csv(path: Path, fast_mode: bool = False):
    if not path.exists():
        print(f"[Train] ERROR: {path} not found.")
        sys.exit(1)

    print(f"[Train] Reading : {path.name}")

    # ── Bucket rows by label (first pass) ─────────────────────────────────────
    buckets:  dict[str, list[list[float]]] = {}
    skipped   = 0
    padded_n  = 0
    col_types: Counter = Counter()

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            line = line.strip()
            if not line: continue

            parts = line.split(",")
            n     = len(parts)
            lbl   = parts[0].strip().upper()

            if n == DUAL_COLS:
                # standard 84-feature row
                try:    vals = [float(v) for v in parts[1:]]
                except: skipped += 1; continue
                col_types["dual (84f)"] += 1

            elif n == SINGLE_COLS:
                # 42-feature row → pad right hand with 42 zeros → 84 features
                try:    vals = [float(v) for v in parts[1:]] + [0.0] * 42
                except: skipped += 1; continue
                padded_n += 1
                col_types["single→padded (42→84f)"] += 1

            else:
                skipped += 1
                col_types[f"bad width ({n})"] += 1
                continue

            # skip all-zero vectors (no hand detected)
            if all(v == 0.0 for v in vals):
                skipped += 1
                continue

            if lbl not in buckets:
                buckets[lbl] = []
            buckets[lbl].append(vals)

    if not buckets:
        print("[Train] ERROR: No valid rows found. Run clean_csv.py first.")
        sys.exit(1)

    # ── Column type report ─────────────────────────────────────────────────────
    print(f"\n[Train] Row types found:")
    for t, cnt in col_types.items():
        print(f"  {t:<32} {cnt:>8,}")
    if padded_n:
        print(f"  → {padded_n:,} single-hand rows auto-padded to 84 features")
    if skipped:
        print(f"  → {skipped:,} rows skipped (bad width / all-zero)")

    # ── Fast mode: per-class sampling (never wipe a class) ────────────────────
    MIN_PER_CLASS = 20
    if fast_mode:
        import random as _r; _r.seed(42)
        for lbl in buckets:
            n_keep = max(MIN_PER_CLASS, len(buckets[lbl]) // 4)
            if len(buckets[lbl]) > n_keep:
                buckets[lbl] = _r.sample(buckets[lbl], n_keep)
        print(f"\n[Train] ⚡ Fast mode: 25% per class, min {MIN_PER_CLASS}")

    # ── Warn on thin classes ───────────────────────────────────────────────────
    MIN_SAFE = 10
    thin = {l: len(v) for l, v in buckets.items() if len(v) < MIN_SAFE}
    if thin:
        print(f"\n[Train] ⚠  Low-sample gestures (< {MIN_SAFE} rows) — collect more:")
        for l, n in sorted(thin.items()):
            print(f"          {l:<26} {n} rows")

    # ── Flatten to arrays ──────────────────────────────────────────────────────
    label_names = sorted(buckets.keys())
    label_to_id = {l: i for i, l in enumerate(label_names)}
    labels_raw, feature_rows = [], []
    for lbl in label_names:
        for vals in buckets[lbl]:
            labels_raw.append(lbl)
            feature_rows.append(vals)

    X = np.array(feature_rows, dtype=np.float32); del feature_rows
    y = np.array([label_to_id[l] for l in labels_raw], dtype=np.int32)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n[Train] Total rows  : {len(X):,}")
    print(f"[Train] Features    : {X.shape[1]}  (unified 84-feature space)")
    print(f"[Train] Gestures    : {len(label_names)}")
    print(f"\n[Train] Class distribution:")
    print(f"  {'Gesture':<28} {'Rows':>8}  {'Bar'}")
    print(f"  {'─'*28} {'─'*8}  {'─'*20}")
    for lbl in label_names:
        cnt  = len(buckets[lbl])
        bar  = "▓" * min(25, cnt // 10)
        flag = "  ⚠ LOW" if cnt < MIN_SAFE else ""
        print(f"  {lbl:<28} {cnt:>8,}  {bar}{flag}")

    return X, y, label_names


# ══════════════════════════════════════════════════════════════════════════════
# MLP trainer
# ══════════════════════════════════════════════════════════════════════════════

def train_mlp(X, y, label_names: list[str], fast_mode: bool = False):
    from sklearn.neural_network import MLPClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.preprocessing import StandardScaler

    n_classes = len(label_names)
    n_rows    = len(X)

    print(f"\n[Train] Algorithm  : MLP Neural Network")
    print(f"[Train] Rows       : {n_rows:,}  |  Features: {X.shape[1]}  |  Classes: {n_classes}")
    print(f"[Train] Sign types : single-hand + dual-hand  (unified 84-feature model)")

    # Scaling — mandatory for MLP convergence
    print("[Train] Scaling …")
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Robust train/test split ────────────────────────────────────────────────
    min_class_n = min(Counter(y).values())
    if min_class_n < 2:
        print(f"[Train] ⚠  Some classes have only 1 sample → train=test (no split)")
        X_tr, X_te, y_tr, y_te = X_scaled, X_scaled, y, y
    else:
        test_size = min(0.15, max(0.05, 2 / min_class_n))
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X_scaled, y, test_size=test_size, random_state=42, stratify=y
            )
        except ValueError as e:
            print(f"[Train] ⚠  Stratified split failed ({e}) → non-stratified")
            X_tr, X_te, y_tr, y_te = train_test_split(
                X_scaled, y, test_size=0.15, random_state=42
            )

    print(f"[Train] Train: {len(X_tr):,}   Test: {len(X_te):,}")

    if fast_mode:
        layers, max_iter, batch = (256, 128), 50, 1024
        print("[Train] ⚡ FAST mode — 2 layers, 50 epochs")
    else:
        layers, max_iter, batch = (512, 256, 128), 200, 512
        print("[Train] FULL mode — 3 layers, up to 200 epochs")

    clf = MLPClassifier(
        hidden_layer_sizes  = layers,
        activation          = "relu",
        solver              = "adam",
        alpha               = 0.0001,
        batch_size          = batch,
        learning_rate       = "adaptive",
        max_iter            = max_iter,
        early_stopping      = True,
        validation_fraction = 0.1,
        n_iter_no_change    = 15,
        random_state        = 42,
        verbose             = True,
    )

    t0 = time.time()
    print("\n[Train] Training …\n")
    clf.fit(X_tr, y_tr)

    # map integer predictions → gesture names for the report
    y_pred_idx   = clf.predict(X_te)
    y_pred_names = [label_names[i] for i in y_pred_idx]
    y_te_names   = [label_names[i] for i in y_te]

    acc = accuracy_score(y_te_names, y_pred_names)
    mins, secs = divmod(int(time.time() - t0), 60)

    print(f"\n[Train] ✓ Done in {mins}m {secs}s")
    print(f"[Train] Accuracy  : {acc*100:.2f}%\n")
    report = classification_report(y_te_names, y_pred_names, zero_division=0)
    print(report)

    return clf, scaler, acc, report


# ══════════════════════════════════════════════════════════════════════════════
# Save bundle — { model, scaler, labels, n_features }
# ══════════════════════════════════════════════════════════════════════════════

def save_bundle(model, scaler, label_names: list[str], n_features: int, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model"      : model,
        "scaler"     : scaler,
        "labels"     : label_names,   # real gesture names, always
        "n_features" : n_features,
    }
    with open(path, "wb") as f:
        pickle.dump(bundle, f, protocol=4)
    with open(path, "rb") as f:
        v = pickle.load(f)
    assert v["labels"] == label_names, "Bundle verification failed!"
    print(f"[Train] Saved model  : {path}")
    print(f"[Train]   labels     : {label_names}")
    print(f"[Train]   n_features : {n_features}")


def save_labels_pkl(label_names: list[str], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(np.array(label_names, dtype=str), f, protocol=4)
    print(f"[Train] Saved labels : {path}")


def save_report(path, label_names, acc, report, n_rows, n_features):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("Arise IVA — Training Report\n")
        f.write(f"Generated  : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Algorithm  : MLPClassifier  (unified single+dual hand)\n")
        f.write(f"Rows       : {n_rows:,}\n")
        f.write(f"Features   : {n_features}  (84 — unified space)\n")
        f.write(f"Labels     : {label_names}\n")
        f.write(f"Accuracy   : {acc*100:.2f}%\n\n")
        f.write(report)
    print(f"[Train] Saved report : {path}")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    fast_mode = "--fast" in sys.argv
    print("\n" + "═"*62)
    print("  Arise IVA — Unified Single + Dual Hand Model Training")
    if fast_mode: print("  ⚡ FAST MODE")
    print("═"*62)

    X, y, label_names = load_csv(DATASET_PATH, fast_mode)
    model, scaler, acc, report = train_mlp(X, y, label_names, fast_mode)

    print("\n[Train] Saving …")
    save_bundle(model, scaler, label_names, X.shape[1], MODEL_PKL)
    save_labels_pkl(label_names, LABELS_PKL)
    save_report(REPORT_PATH, label_names, acc, report, len(X), X.shape[1])

    print(f"\n[Train] ✓  Accuracy : {acc*100:.2f}%")
    print(f"[Train]    Gestures : {label_names}")
    print(f"[Train]    Run  python app/main.py  to start.\n")


if __name__ == "__main__":
    main()