"""
arise-iva | CSV Label Cleaner
==============================
Removes rows with incorrect/unwanted labels from the dataset CSV.
Use this before re-running extraction to avoid duplicate/corrupt data.

Usage
-----
    cd arise-iva
    python scripts/clean_bad_labels.py
"""

from __future__ import annotations
import os, sys, shutil, time
from pathlib import Path

import pandas as pd

_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
DATASET_CSV  = _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"


def main() -> None:
    print("\n" + "=" * 54)
    print("   Arise IVA  —  CSV Label Cleaner")
    print("=" * 54)

    if not DATASET_CSV.exists():
        print(f"\n[Cleaner] No CSV found at: {DATASET_CSV}")
        print("          Nothing to clean.")
        sys.exit(0)

    # ── Load & audit ───────────────────────────────────────────────────────────
    # Read raw to avoid pandas width-mismatch crash
    rows = []
    header_line = ""
    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n\r")
            if i == 0:
                header_line = line
                continue
            if line.strip():
                rows.append(line)

    if not rows:
        print("[Cleaner] CSV is empty (header only). Nothing to clean.")
        sys.exit(0)

    # Count labels
    from collections import Counter
    label_counts = Counter(line.split(",")[0].strip().upper() for line in rows)

    print(f"\n[Cleaner] Current label distribution ({len(rows)} total rows):")
    print(f"  {'Label':<28} {'Count':>6}")
    print(f"  {'─'*28} {'─'*6}")
    for lbl, cnt in sorted(label_counts.items(), key=lambda x: -x[1]):
        flag = "  ← WRONG" if lbl == "SL" else ""
        print(f"  {lbl:<28} {cnt:>6}{flag}")

    # ── Ask which labels to remove ─────────────────────────────────────────────
    print("\n[Cleaner] Which labels should be removed?")
    print("          Press ENTER to remove 'SL' (default),")
    raw = input("          or type comma-separated labels (e.g. SL,UNKNOWN): ").strip()

    if not raw:
        bad_labels = {"SL"}
    else:
        bad_labels = {l.strip().upper() for l in raw.split(",") if l.strip()}

    print(f"\n[Cleaner] Removing labels: {sorted(bad_labels)}")

    # ── Backup ────────────────────────────────────────────────────────────────
    backup = DATASET_CSV.parent / f"gesture_dataset_backup_{int(time.time())}.csv"
    shutil.copy2(DATASET_CSV, backup)
    print(f"[Cleaner] Backup saved  : {backup.name}")

    # ── Filter ────────────────────────────────────────────────────────────────
    kept    = []
    removed = 0
    for line in rows:
        lbl = line.split(",")[0].strip().upper()
        if lbl in bad_labels:
            removed += 1
        else:
            kept.append(line)

    # ── Write clean CSV ────────────────────────────────────────────────────────
    with open(DATASET_CSV, "w", encoding="utf-8") as f:
        f.write(header_line + "\n")
        for line in kept:
            f.write(line + "\n")

    print(f"\n[Cleaner] ✓ Done:")
    print(f"           Rows removed : {removed}")
    print(f"           Rows kept    : {len(kept)}")
    print(f"           CSV saved    : {DATASET_CSV}")
    print(f"\n[Cleaner] Now run:")
    print(f"           python scripts/extract_landmarks_from_videos.py")
    print(f"           python scripts/train_model.py\n")


if __name__ == "__main__":
    main()
    