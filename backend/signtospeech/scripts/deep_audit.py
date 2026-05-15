"""
arise-iva | Deep Data Audit
Finds exactly why accuracy is 17%.
    python scripts/deep_audit.py
"""
from __future__ import annotations
import sys, os
from pathlib import Path
from collections import Counter
import numpy as np

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_DIR / "app"))
CSV_PATH = _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

print("\n" + "═"*64)
print("  ARISE IVA — DEEP DATA AUDIT")
print("═"*64)

# ── Read CSV ───────────────────────────────────────────────────────────────────
rows_by_label: dict[str, list] = {}
total = bad = zero_rows = 0

with open(CSV_PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i == 0:
            ncols = len(line.strip().split(","))
            print(f"\nCSV columns : {ncols}  ({'dual 84f' if ncols==85 else 'single 42f' if ncols==43 else '???'})")
            continue
        line = line.strip()
        if not line: continue
        total += 1
        parts = line.split(",")
        if len(parts) != ncols:
            bad += 1; continue
        lbl = parts[0].strip().upper()
        try:
            vals = [float(v) for v in parts[1:]]
        except:
            bad += 1; continue
        if all(v == 0.0 for v in vals):
            zero_rows += 1; continue
        if lbl not in rows_by_label:
            rows_by_label[lbl] = []
        rows_by_label[lbl].append(vals)

n_labels = len(rows_by_label)
total_valid = sum(len(v) for v in rows_by_label.values())

print(f"Total rows  : {total:,}")
print(f"Valid rows  : {total_valid:,}")
print(f"Zero rows   : {zero_rows:,}  ← frames with no hand detected (wasted)")
print(f"Bad rows    : {bad:,}")
print(f"Labels      : {n_labels}")
print(f"\nRandom guess accuracy would be: {100/n_labels:.1f}%")
print(f"Your accuracy was 17% → {'RANDOM CHANCE' if abs(100/n_labels - 17) < 5 else 'slightly above random'}")

# ── Feature range per label ────────────────────────────────────────────────────
print(f"\n{'─'*64}")
print("Feature value ranges per label (should be -1.0 to 1.0):")
print(f"{'Label':<28} {'Min':>8} {'Max':>8} {'Std':>8} {'Rows':>8}  Status")
print(f"{'─'*28} {'─'*8} {'─'*8} {'─'*8} {'─'*8}  {'─'*12}")

problems = []
for lbl in sorted(rows_by_label.keys())[:30]:  # show first 30
    arr = np.array(rows_by_label[lbl], dtype=np.float32)
    mn, mx, std = float(arr.min()), float(arr.max()), float(arr.std())
    n = len(arr)
    
    if mx > 100 or mn < -100:
        status = "BAD RANGE ✗"
        problems.append((lbl, f"extreme values: [{mn:.1f}, {mx:.1f}]"))
    elif mx - mn < 0.001:
        status = "NO VARIANCE ✗"
        problems.append((lbl, "all values identical — no hand detected"))
    elif std < 0.01:
        status = "TINY STD ✗"
        problems.append((lbl, f"std={std:.4f} — almost no variation"))
    elif mx <= 1.01 and mn >= -1.01:
        status = "OK ✓"
    else:
        status = f"RANGE WARN ⚠"
    
    print(f"{lbl:<28} {mn:>8.3f} {mx:>8.3f} {std:>8.4f} {n:>8,}  {status}")

if n_labels > 30:
    print(f"  ... and {n_labels-30} more labels")

# ── Check if features DIFFER between labels (most important test) ──────────────
print(f"\n{'─'*64}")
print("Inter-class separability (do different gestures look different?):")

# Take the MEAN vector of each class
label_means = {}
for lbl, rows in rows_by_label.items():
    label_means[lbl] = np.mean(rows, axis=0)

lbls = sorted(label_means.keys())
if len(lbls) >= 2:
    # Compare first few classes pairwise
    pairs_checked = 0
    identical_pairs = 0
    for i in range(min(5, len(lbls))):
        for j in range(i+1, min(5, len(lbls))):
            a, b = label_means[lbls[i]], label_means[lbls[j]]
            dist = float(np.linalg.norm(a - b))
            pairs_checked += 1
            if dist < 0.05:
                identical_pairs += 1
                print(f"  ✗ {lbls[i]:<20} vs {lbls[j]:<20} distance={dist:.4f} ← IDENTICAL (bad!)")
            else:
                print(f"  ✓ {lbls[i]:<20} vs {lbls[j]:<20} distance={dist:.4f}")
    
    if identical_pairs > 0:
        problems.append(("SEPARABILITY", f"{identical_pairs}/{pairs_checked} class pairs are identical"))

# ── Check if videos had hands at all ──────────────────────────────────────────
print(f"\n{'─'*64}")
hand_detected_pct = total_valid / max(1, total_valid + zero_rows) * 100
print(f"Frames with hand detected : {hand_detected_pct:.1f}%")
if hand_detected_pct < 50:
    print(f"  ✗ CRITICAL: Less than 50% of frames had a hand!")
    print(f"    MediaPipe failed to detect hands in most of your videos.")
    problems.append(("DETECTION", f"Only {hand_detected_pct:.0f}% of frames had a detectable hand"))

# ── VERDICT ────────────────────────────────────────────────────────────────────
print(f"\n{'═'*64}")
print("VERDICT:")

if not problems:
    print("  Data looks OK. Problem is in training or prediction code.")
else:
    print(f"  Found {len(problems)} critical problems:\n")
    for item, reason in problems:
        print(f"  ✗ {item}: {reason}")
    
    print(f"\n  ROOT CAUSE SUMMARY:")
    
    if zero_rows > total_valid * 0.3:
        print(f"  → {zero_rows:,} zero rows = MediaPipe couldn't see hands in your videos")
        print(f"    Videos may be low quality, hands obscured, or wrong format")
    
    if n_labels > 50:
        print(f"  → {n_labels} classes with only {total_valid//n_labels:,} avg rows each")
        print(f"    Need at least 500 rows per class for reliable training")
    
    print(f"\n  RECOMMENDED FIX:")
    print(f"  Don't use video extraction. Collect data live from webcam instead:")
    print(f"  1. Delete the current CSV")
    print(f"  2. python scripts/collect_data.py  (collect 300+ per gesture)")
    print(f"  3. python scripts/train_model.py --fast  (verify it works)")
    print(f"  4. python scripts/train_model.py  (full train)")

print("═"*64 + "\n")