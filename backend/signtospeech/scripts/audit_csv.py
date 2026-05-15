"""
arise-iva | CSV Data Auditor
Run this BEFORE retraining. It tells you if your training data is valid.

    cd arise-iva
    python scripts/audit_csv.py
"""
from __future__ import annotations
import sys, os
from pathlib import Path
from collections import Counter
import numpy as np

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
CSV_PATH     = _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

print("\n" + "═"*60)
print("  ARISE IVA — CSV DATA AUDIT")
print("═"*60)

if not CSV_PATH.exists():
    print(f"CSV not found: {CSV_PATH}"); sys.exit(1)

# ── Read first data row to detect format ──────────────────────────────────────
rows_by_label: dict[str, list[list[float]]] = {}
bad_rows = 0
zero_rows = 0
total = 0

print(f"\nReading: {CSV_PATH}")

with open(CSV_PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i == 0:
            header = line.strip()
            n_header_cols = len(header.split(","))
            print(f"Header cols: {n_header_cols}")
            continue

        line = line.strip()
        if not line: continue
        total += 1

        parts = line.split(",")
        lbl   = parts[0].strip().upper()

        try:
            vals = [float(v) for v in parts[1:]]
        except ValueError:
            bad_rows += 1
            continue

        # Check if entire feature vector is zeros (no hand detected rows saved)
        if all(v == 0.0 for v in vals):
            zero_rows += 1
            continue

        if lbl not in rows_by_label:
            rows_by_label[lbl] = []
        if len(rows_by_label[lbl]) < 100:   # keep up to 100 rows per label for analysis
            rows_by_label[lbl].append(vals)

print(f"\n{'─'*60}")
print(f"  Total rows         : {total:,}")
print(f"  Bad rows (parse)   : {bad_rows:,}")
print(f"  All-zero rows      : {zero_rows:,}  ← these are wasted samples (no hand)")
print(f"  Labels found       : {len(rows_by_label)}")

# ── Per-label stats ────────────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  {'Label':<24} {'Samples':>8}  {'FeatureRange':>14}  {'AllZero?':>8}")
print(f"  {'─'*24} {'─'*8}  {'─'*14}  {'─'*8}")

problems = []
for lbl in sorted(rows_by_label.keys()):
    rows  = rows_by_label[lbl]
    arr   = np.array(rows, dtype=np.float32)
    fmin  = float(arr.min())
    fmax  = float(arr.max())
    frange = f"[{fmin:.2f}, {fmax:.2f}]"

    # Problem detection
    all_zero = (fmax == 0.0 and fmin == 0.0)
    tiny_range = (fmax - fmin) < 0.01
    bad_range  = fmax > 10.0 or fmin < -10.0   # normalised values should be -1..1

    flag = ""
    if all_zero:   flag = "ALL ZERO ✗"; problems.append((lbl, "all zero values"))
    elif bad_range: flag = "BAD RANGE ✗"; problems.append((lbl, f"values out of -1..1: {frange}"))
    elif tiny_range: flag = "TINY RANGE ⚠"; problems.append((lbl, "almost no variation"))

    print(f"  {lbl:<24} {len(rows):>8}  {frange:>14}  {flag}")

# ── Sample 3 actual feature vectors ───────────────────────────────────────────
print(f"\n{'─'*60}")
print("  Sample feature vectors (first 3 gestures, first row each):")
for lbl in list(sorted(rows_by_label.keys()))[:3]:
    v = rows_by_label[lbl][0][:10]
    print(f"\n  {lbl}: {[round(x,3) for x in v]} ...")
    # Valid landmarks should be roughly in -1..1 range
    # and NOT all the same value
    unique_vals = len(set(round(x, 4) for x in rows_by_label[lbl][0]))
    print(f"         unique values in row: {unique_vals}  (should be >15 for real landmarks)")
    if unique_vals < 5:
        problems.append((lbl, f"only {unique_vals} unique values — looks like bad data"))

# ── Verdict ────────────────────────────────────────────────────────────────────
print(f"\n{'═'*60}")
if not problems:
    print("  ✓  Data looks VALID — values in expected range, variation present")
    print("  The issue is in model training or prediction code, not the data.")
    print("\n  Next step: python scripts/train_model.py")
else:
    print(f"  ✗  Found {len(problems)} DATA PROBLEMS:\n")
    for lbl, reason in problems:
        print(f"     • {lbl}: {reason}")
    print("\n  Root cause: bad normalisation during extraction OR")
    print("  rows saved when no hand was detected.")
    print("\n  Fix options:")
    print("  1. Delete CSV and re-extract: python scripts/extract_landmarks_from_videos.py")
    print("  2. Re-collect from webcam:    python scripts/collect_data.py")

print("═"*60 + "\n")