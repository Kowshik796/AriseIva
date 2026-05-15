"""
arise-iva | clean_csv.py  — Smart Cleaner + Mixed-Width Fixer
=============================================================
Handles ALL row types in your CSV:

  85-col rows  (dual-hand)   → kept as-is            ✓
  43-col rows  (single-hand) → padded to 85 cols      ✓  (right hand zeroed)
  all-zero feature rows      → removed                ✗
  unparseable / other widths → removed                ✗

This means gestures collected in single-hand mode (like THINK) are
preserved and padded — NOT discarded.

Usage
-----
    python scripts/clean_csv.py
    python scripts/clean_csv.py --csv path\\to\\file.csv
"""
from __future__ import annotations
import sys, shutil, time
from pathlib import Path
from collections import Counter

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent

_csv_arg = next((sys.argv[i+1] for i, a in enumerate(sys.argv)
                 if a == "--csv" and i+1 < len(sys.argv)), None)
TARGET_CSV = Path(_csv_arg) if _csv_arg else \
             _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

DUAL_COLS   = 85   # label + 84 features
SINGLE_COLS = 43   # label + 42 features
ZERO_PAD    = ",0.0" * 42   # 42 zeros appended to single-hand rows

print("\n" + "═"*62)
print("  Arise IVA — Smart CSV Cleaner")
print("═"*62)

if not TARGET_CSV.exists():
    print(f"\n✗  File not found: {TARGET_CSV}")
    sys.exit(1)

# ── Read ───────────────────────────────────────────────────────────────────────
header_line = ""
all_rows    = []
with open(TARGET_CSV, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        raw = line.rstrip("\n\r")
        if i == 0:
            header_line = raw
            continue
        if raw.strip():
            all_rows.append(raw)

print(f"\n  File        : {TARGET_CSV.name}")
print(f"  Total rows  : {len(all_rows):,}")

# ── Classify every row ─────────────────────────────────────────────────────────
kept_dual   = []   # already 85-col
padded      = []   # was 43-col, padded to 85-col
removed     = []
reasons: Counter = Counter()
label_action: dict[str, Counter] = {}   # label → {kept/padded/removed: count}

def track(lbl, action):
    if lbl not in label_action:
        label_action[lbl] = Counter()
    label_action[lbl][action] += 1

for row in all_rows:
    parts = row.split(",")
    n     = len(parts)
    lbl   = parts[0].strip().upper()

    if n == DUAL_COLS:
        try:
            vals = [float(v) for v in parts[1:]]
        except ValueError:
            removed.append(row); reasons["unparseable"] += 1; track(lbl,"removed"); continue

        if all(v == 0.0 for v in vals):
            removed.append(row); reasons["all-zero (no hand)"] += 1; track(lbl,"removed"); continue

        kept_dual.append(row)
        track(lbl, "kept")

    elif n == SINGLE_COLS:
        try:
            vals = [float(v) for v in parts[1:]]
        except ValueError:
            removed.append(row); reasons["unparseable"] += 1; track(lbl,"removed"); continue

        if all(v == 0.0 for v in vals):
            removed.append(row); reasons["all-zero (no hand)"] += 1; track(lbl,"removed"); continue

        # Pad with 42 zeros for the missing (right) hand → makes it 85-col
        padded_row = row + ZERO_PAD
        padded.append(padded_row)
        track(lbl, "padded")

    else:
        removed.append(row)
        reasons[f"wrong width ({n} cols)"] += 1
        track(lbl, "removed")

all_output = kept_dual + padded

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\n  Result breakdown:")
print(f"    Dual-hand rows kept   (85-col) : {len(kept_dual):>8,}")
print(f"    Single-hand rows padded(43→85) : {len(padded):>8,}  ← preserved, not discarded")
print(f"    Rows removed                   : {len(removed):>8,}")
for reason, cnt in reasons.items():
    print(f"      • {reason:<32} {cnt:,}")
print(f"    ─────────────────────────────────────────")
print(f"    Total output rows              : {len(all_output):>8,}")

print(f"\n  Per-gesture summary:")
print(f"  {'Gesture':<28} {'Kept':>6} {'Padded':>8} {'Removed':>8}  Total")
print(f"  {'─'*28} {'─'*6} {'─'*8} {'─'*8}  ─────")

all_labels = sorted(label_action.keys())
for lbl in all_labels:
    c = label_action[lbl]
    kept_n    = c.get("kept",    0)
    padded_n  = c.get("padded",  0)
    removed_n = c.get("removed", 0)
    total     = kept_n + padded_n
    flag      = "  ← ALL REMOVED ✗" if total == 0 else ""
    print(f"  {lbl:<28} {kept_n:>6,} {padded_n:>8,} {removed_n:>8,}  {total:>5,}{flag}")

if not removed and not padded:
    print("\n  ✓  CSV is already clean and uniform. Nothing to do.")
    sys.exit(0)

# ── Confirm ────────────────────────────────────────────────────────────────────
print()
print(f"  Actions:")
if padded:   print(f"    • Pad {len(padded):,} single-hand rows to 85 cols (add right-hand zeros)")
if removed:  print(f"    • Remove {len(removed):,} bad rows (all-zero / unparseable / wrong width)")
print()
ans = input("  Apply changes and save? [Y/n]: ").strip().lower()
if ans not in ("", "y", "yes"):
    print("  Cancelled."); sys.exit(0)

# ── Build correct dual-hand header ─────────────────────────────────────────────
dual_header = "label"
for p in ["L", "R"]:
    for i in range(21):
        dual_header += f",{p}x{i},{p}y{i}"

# ── Backup ─────────────────────────────────────────────────────────────────────
backup = TARGET_CSV.parent / f"{TARGET_CSV.stem}_backup_{int(time.time())}.csv"
shutil.copy2(TARGET_CSV, backup)
print(f"\n  Backup saved : {backup.name}")

# ── Write ──────────────────────────────────────────────────────────────────────
with open(TARGET_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(dual_header + "\n")
    for row in all_output:
        f.write(row + "\n")

print(f"  Saved       : {TARGET_CSV}")
print(f"\n  ✓  {len(padded):,} rows padded  |  {len(removed):,} rows removed  |  {len(all_output):,} total kept")
print(f"\n  Next step:")
print(f"  python scripts/train_model.py --csv \"{TARGET_CSV}\"\n")