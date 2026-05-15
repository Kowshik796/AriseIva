"""
arise-iva | Label Remapper
===========================
Renames numeric labels (0, 1, 2 …) in the CSV to real gesture names.

Usage
-----
    python scripts/remap_labels.py

You will be prompted to enter the name for each numeric label.
A remapped copy of the CSV is saved, then you retrain on it.
"""
from __future__ import annotations
import sys, shutil, time
from pathlib import Path

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent

CSV_DIR  = _PROJECT_DIR / "dataset" / "processed_landmarks"

print("\n" + "═"*58)
print("  Arise IVA — Label Remapper")
print("═"*58)

# ── Find all CSVs in the landmarks folder ──────────────────────────────────────
csvs = sorted(CSV_DIR.glob("*.csv"))
if not csvs:
    print(f"No CSV files found in {CSV_DIR}"); sys.exit(1)

print("\nAvailable CSV files:")
for i, p in enumerate(csvs):
    size = p.stat().st_size // 1024
    print(f"  [{i}] {p.name}  ({size:,} KB)")

idx = input("\nWhich file to remap? [0]: ").strip()
src = csvs[int(idx) if idx.isdigit() else 0]
print(f"\nSelected: {src.name}")

# ── Detect all unique labels ───────────────────────────────────────────────────
label_set: set[str] = set()
ncols = 0
with open(src, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i == 0:
            ncols = len(line.strip().split(","))
            continue
        parts = line.strip().split(",")
        if len(parts) == ncols:
            label_set.add(parts[0].strip())

labels_sorted = sorted(label_set, key=lambda x: int(x) if x.isdigit() else x)

print(f"\nFound {len(labels_sorted)} unique labels: {labels_sorted}")
print(f"\nEnter the GESTURE NAME for each label.")
print("(Press ENTER to keep the label as-is, e.g. already named correctly)\n")

# ── Build mapping ──────────────────────────────────────────────────────────────
mapping: dict[str, str] = {}
for lbl in labels_sorted:
    name = input(f"  Label '{lbl}' → gesture name: ").strip().upper()
    mapping[lbl] = name if name else lbl.upper()

print(f"\nMapping:")
for k, v in mapping.items():
    print(f"  {k:>4} → {v}")

confirm = input("\nApply this mapping? [Y/n]: ").strip().lower()
if confirm == "n":
    print("Cancelled."); sys.exit(0)

# ── Backup original ────────────────────────────────────────────────────────────
backup = CSV_DIR / f"{src.stem}_before_remap_{int(time.time())}.csv"
shutil.copy2(src, backup)
print(f"\nBackup saved: {backup.name}")

# ── Write remapped CSV ─────────────────────────────────────────────────────────
out_path = CSV_DIR / "gesture_dataset.csv"
remapped = 0
skipped  = 0

with open(src, "r", encoding="utf-8") as fin, \
     open(out_path, "w", encoding="utf-8", newline="") as fout:
    for i, line in enumerate(fin):
        if i == 0:
            fout.write(line)   # keep header
            continue
        line_s = line.strip()
        if not line_s:
            continue
        parts = line_s.split(",")
        if len(parts) != ncols:
            skipped += 1
            continue
        old_lbl = parts[0].strip()
        new_lbl = mapping.get(old_lbl, old_lbl.upper())
        parts[0] = new_lbl
        fout.write(",".join(parts) + "\n")
        remapped += 1

print(f"\n✓ Remapped {remapped:,} rows  (skipped {skipped})")
print(f"  Saved to: {out_path}")
print(f"\nNext steps:")
print(f"  python scripts/train_model.py")
print(f"  python app/main.py\n")