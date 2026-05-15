"""
arise-iva | CSV Migration Script
=================================
Converts a mixed CSV (43-col single-hand + 85-col dual-hand rows) into a
unified 85-col dataset where every row has the same width.

Single-hand rows  (43 cols) → padded with 42 zeros → 85 cols
Dual-hand rows    (85 cols) → kept as-is
Malformed rows    (other)   → dropped with a warning

Run this ONCE to unify your existing dataset, then retrain.

Usage
-----
    cd arise-iva
    python scripts/migrate_csv.py
"""

from __future__ import annotations
import os
import sys
import shutil
import time

# ── Paths ──────────────────────────────────────────────────────────────────────
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
_LANDMARKS   = os.path.join(_PROJECT_DIR, "dataset", "processed_landmarks")

SRC_CSV      = os.path.join(_LANDMARKS, "gesture_dataset.csv")
BACKUP_CSV   = os.path.join(_LANDMARKS, f"gesture_dataset_backup_{int(time.time())}.csv")
OUT_CSV      = SRC_CSV   # overwrite in-place (backup kept)

SINGLE_COLS  = 43        # label + 42 single-hand features
DUAL_COLS    = 85        # label + 84 dual-hand features
ZERO_PAD     = ",0.0" * 42  # 42 zeros appended to single-hand rows


def _dual_header() -> str:
    """Build the 85-column header line."""
    cols = ["label"]
    for p in ["L", "R"]:
        for i in range(21):
            cols += [f"{p}x{i}", f"{p}y{i}"]
    return ",".join(cols)


def migrate() -> None:
    print("\n" + "=" * 58)
    print("   Arise IVA  —  CSV Migration (Single → Dual Format)")
    print("=" * 58)

    if not os.path.isfile(SRC_CSV):
        print(f"[Migrate] ERROR: CSV not found: {SRC_CSV}")
        sys.exit(1)

    # ── Backup original ────────────────────────────────────────────────────────
    shutil.copy2(SRC_CSV, BACKUP_CSV)
    print(f"[Migrate] Backup saved : {BACKUP_CSV}")

    # ── Read & audit ───────────────────────────────────────────────────────────
    single_count = 0
    dual_count   = 0
    dropped      = 0
    out_rows     = []

    with open(SRC_CSV, "r", newline="", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n\r")
            if i == 0:
                continue                      # skip old header

            if not line.strip():
                continue                      # skip blank lines

            n_cols = len(line.split(","))

            if n_cols == SINGLE_COLS:
                # Pad the absent hand with 42 zeros
                out_rows.append(line + ZERO_PAD)
                single_count += 1

            elif n_cols == DUAL_COLS:
                out_rows.append(line)
                dual_count += 1

            else:
                dropped += 1
                if dropped <= 5:
                    print(f"[Migrate]   Dropped row {i+1}: {n_cols} cols — '{line[:60]}…'")

    if dropped > 5:
        print(f"[Migrate]   … and {dropped - 5} more malformed rows dropped.")

    # ── Write unified CSV ──────────────────────────────────────────────────────
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        f.write(_dual_header() + "\n")
        for row in out_rows:
            f.write(row + "\n")

    total = single_count + dual_count
    print(f"\n[Migrate] ✓ Migration complete:")
    print(f"          Single-hand rows padded : {single_count}")
    print(f"          Dual-hand rows kept     : {dual_count}")
    print(f"          Malformed rows dropped  : {dropped}")
    print(f"          Total rows written      : {total}")
    print(f"          Output CSV              : {OUT_CSV}")
    print(f"\n[Migrate]   Now run:  python scripts/train_model.py\n")


if __name__ == "__main__":
    migrate()