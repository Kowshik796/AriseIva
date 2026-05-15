"""
arise-iva | Video & Image → Landmark Dataset Extractor
=======================================================
Converts gesture video clips AND still images into hand landmark rows,
then appends them to the existing CSV dataset.

Supported input types
---------------------
  Videos : .mp4  .avi  .mov  .mkv  .webm
  Images : .jpg  .jpeg .png  .bmp  .webp  .tiff

Folder layout (videos and images can be mixed freely)
------------------------------------------------------
    dataset/gesture_videos/
    ├── hello.mp4           → label: HELLO   (root file → filename as label)
    ├── help.png            → label: HELP
    └── YES/
        ├── yes_clip.mp4    → label: YES     (subfolder file → folder as label)
        ├── yes_photo1.jpg  → label: YES
        └── yes_photo2.png  → label: YES
    └── THANK_YOU/
        └── clip.avi        → label: THANK_YOU

Output format (auto-detected from existing CSV)
-----------------------------------------------
  Single-hand  →  43 cols  (label + 42 features)
  Dual-hand    →  85 cols  (label + 84 features, absent hand zero-padded)

Frame sampling (videos only)
-----------------------------
  FRAME_SKIP = 3  →  every 3rd frame processed to reduce near-duplicates
  Images are always processed fully (1 frame = 1 sample, no skipping needed)

Usage
-----
    cd arise-iva
    python scripts/extract_landmarks_from_videos.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

# ── Project paths ──────────────────────────────────────────────────────────────
_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent

VIDEOS_ROOT  = _PROJECT_DIR / "dataset" / "gesture_videos"
DATASET_CSV  = _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

# ── Sampling ───────────────────────────────────────────────────────────────────
FRAME_SKIP = 3   # for videos: process every Nth frame

# ── Supported file extensions ──────────────────────────────────────────────────
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}
ALL_EXTS   = VIDEO_EXTS | IMAGE_EXTS

# ── MediaPipe settings ─────────────────────────────────────────────────────────
MP_MAX_HANDS      = 2
MP_DETECTION_CONF = 0.5

# ── Column counts ──────────────────────────────────────────────────────────────
SINGLE_COLS = 43
DUAL_COLS   = 85
ZERO_PAD_42 = [0.0] * 42


# ══════════════════════════════════════════════════════════════════════════════
# CSV helpers
# ══════════════════════════════════════════════════════════════════════════════

def _detect_csv_mode(path: Path) -> int:
    """Peek at first data row to detect column count. Defaults to DUAL_COLS."""
    if not path.exists():
        return DUAL_COLS
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            n = len(line.strip().split(","))
            if n in (SINGLE_COLS, DUAL_COLS):
                return n
    return DUAL_COLS


def _build_header(total_cols: int) -> list[str]:
    cols = ["label"]
    if total_cols == DUAL_COLS:
        for p in ["L", "R"]:
            for i in range(21):
                cols += [f"{p}x{i}", f"{p}y{i}"]
    else:
        for i in range(21):
            cols += [f"x{i}", f"y{i}"]
    return cols


def _load_existing_csv(path: Path, target_cols: int) -> pd.DataFrame:
    header = _build_header(target_cols)
    if not path.exists():
        return pd.DataFrame(columns=header)
    try:
        df = pd.read_csv(path, header=0)
        orig = len(df)
        df   = df[df.apply(lambda r: r.notna().sum(), axis=1) == (target_cols - 1)]
        if len(df) < orig:
            print(f"[Extractor] ⚠  Dropped {orig - len(df)} rows with wrong column count.")
        return df
    except Exception as exc:
        print(f"[Extractor] ⚠  Could not read existing CSV ({exc}). Starting fresh.")
        return pd.DataFrame(columns=header)


# ══════════════════════════════════════════════════════════════════════════════
# Landmark normalisation
# ══════════════════════════════════════════════════════════════════════════════

def _normalise_hand(hand_landmarks) -> list[float]:
    """Wrist-translate + max-scale → flat 42-float list."""
    coords = np.array(
        [[lm.x, lm.y] for lm in hand_landmarks.landmark],
        dtype=np.float32,
    )
    coords -= coords[0]
    max_val = np.abs(coords).max()
    if max_val > 0:
        coords /= max_val
    return [round(float(v), 6) for v in coords.flatten()]


def _build_single_vector(results) -> Optional[list[float]]:
    if not results or not results.multi_hand_landmarks:
        return None
    return _normalise_hand(results.multi_hand_landmarks[0])


def _build_dual_vector(results) -> Optional[list[float]]:
    if not results or not results.multi_hand_landmarks:
        return None
    left_vec  = list(ZERO_PAD_42)
    right_vec = list(ZERO_PAD_42)
    for hand_lm, handedness in zip(
        results.multi_hand_landmarks, results.multi_handedness
    ):
        label = handedness.classification[0].label
        vec   = _normalise_hand(hand_lm)
        if label == "Left":
            left_vec = vec
        else:
            right_vec = vec
    return left_vec + right_vec


def _extract_vector(results, target_cols: int) -> Optional[list[float]]:
    """Dispatch to the correct vector builder based on target_cols."""
    return (_build_dual_vector(results) if target_cols == DUAL_COLS
            else _build_single_vector(results))


# ══════════════════════════════════════════════════════════════════════════════
# File discovery
# ══════════════════════════════════════════════════════════════════════════════

def _discover_files(root: Path) -> list[tuple[str, Path, str]]:
    """
    Walk *root* recursively and return (label, path, kind) tuples.

    Label rule: always use the IMMEDIATE PARENT FOLDER of each file.
    This correctly handles any nesting depth:

        gesture_videos/hello.mp4            -> label: HELLO
        gesture_videos/YES/yes.mp4          -> label: YES
        gesture_videos/SL/a lot/clip.mp4    -> label: A LOT
        gesture_videos/SL/above/img.png     -> label: ABOVE
        gesture_videos/SL/a/video.mp4       -> label: A

    The top-level grouping folder (e.g. SL) is automatically skipped
    because it is never the immediate parent of a media file.
    """
    found: list[tuple[str, Path, str]] = []

    if not root.exists():
        return found

    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        ext = item.suffix.lower()
        if ext not in ALL_EXTS:
            continue

        parent = item.parent

        if parent == root:
            # File sits directly in root -> use filename stem
            label = item.stem.upper()
        else:
            # Use the IMMEDIATE parent folder name as the label.
            # This works for any depth: SL/a/clip.mp4 -> parent.name = "a"
            label = parent.name.upper()

        # Normalise whitespace (e.g. "A  LOT" -> "A LOT")
        label = " ".join(label.split())

        kind = "video" if ext in VIDEO_EXTS else "image"
        found.append((label, item, kind))

    return found


# ══════════════════════════════════════════════════════════════════════════════
# Processors
# ══════════════════════════════════════════════════════════════════════════════

def _process_image(
    img_path: Path,
    label: str,
    hands_static,       # MediaPipe Hands initialised with static_image_mode=True
    target_cols: int,
) -> list[list]:
    """
    Extract one landmark row from a still image.

    Uses static_image_mode=True so MediaPipe runs full detection (not tracking),
    which is more accurate for single frames.

    Returns a list containing 0 or 1 rows.
    """
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"  [!] Could not load image: {img_path.name} — skipping.")
        return []

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands_static.process(rgb)

    vector = _extract_vector(results, target_cols)
    if vector is None:
        return []

    return [[label] + vector]


def _process_video(
    video_path: Path,
    label: str,
    hands_video,        # MediaPipe Hands with static_image_mode=False
    target_cols: int,
) -> list[list]:
    """
    Extract landmark rows from every FRAME_SKIP-th frame of a video.
    Skips frames where no hand is detected without crashing.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  [!] Could not open video: {video_path.name} — skipping.")
        return []

    total_frames  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    rows: list[list] = []
    frame_idx     = 0
    no_hand_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Only process every FRAME_SKIP-th frame
        if frame_idx % FRAME_SKIP != 0:
            frame_idx += 1
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = hands_video.process(rgb)
        rgb.flags.writeable = True

        vector = _extract_vector(results, target_cols)
        if vector is None:
            no_hand_count += 1
        else:
            rows.append([label] + vector)

        frame_idx += 1

    cap.release()

    processed = max(1, frame_idx // FRAME_SKIP)
    print(f"    Frames processed : {processed:>5}  (of {total_frames}, skip={FRAME_SKIP})")
    print(f"    Rows extracted   : {len(rows):>5}  "
          f"(skipped {no_hand_count} — no hand detected)")
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n" + "=" * 62)
    print("   Arise IVA  —  Video & Image → Landmark Extractor")
    print("=" * 62)

    if not VIDEOS_ROOT.exists():
        print(f"\n[Extractor] Input folder not found: {VIDEOS_ROOT}")
        print("            Create it, add your videos/images, then re-run.")
        sys.exit(1)

    # ── Discover all files ─────────────────────────────────────────────────────
    file_list = _discover_files(VIDEOS_ROOT)
    if not file_list:
        print(f"\n[Extractor] No supported files found under: {VIDEOS_ROOT}")
        print(f"            Videos : {VIDEO_EXTS}")
        print(f"            Images : {IMAGE_EXTS}")
        sys.exit(1)

    videos = [(l, p) for l, p, k in file_list if k == "video"]
    images = [(l, p) for l, p, k in file_list if k == "image"]

    print(f"\n[Extractor] Discovered:")
    print(f"            Videos : {len(videos)}")
    print(f"            Images : {len(images)}")
    print(f"            Total  : {len(file_list)}\n")

    for label, path, kind in file_list:
        icon = "🎬" if kind == "video" else "🖼 "
        print(f"  {icon}  {label:<22} ← {path.relative_to(_PROJECT_DIR)}")

    # ── Detect CSV format ──────────────────────────────────────────────────────
    target_cols = _detect_csv_mode(DATASET_CSV)
    mode_name   = ("dual-hand (84 features)" if target_cols == DUAL_COLS
                   else "single-hand (42 features)")
    print(f"\n[Extractor] CSV format  : {mode_name}")
    print(f"[Extractor] Output CSV  : {DATASET_CSV}")

    existing_df  = _load_existing_csv(DATASET_CSV, target_cols)
    existing_len = len(existing_df)
    print(f"[Extractor] Existing rows : {existing_len}")

    # ── Initialise MediaPipe — two instances for different modes ───────────────
    # static_image_mode=True  → full detection per frame (best for images)
    # static_image_mode=False → tracking between frames  (best for video)
    mp_hands_mod  = mp.solutions.hands

    hands_static = mp_hands_mod.Hands(
        static_image_mode=True,
        max_num_hands=MP_MAX_HANDS,
        min_detection_confidence=MP_DETECTION_CONF,
    )
    hands_video = mp_hands_mod.Hands(
        static_image_mode=False,
        max_num_hands=MP_MAX_HANDS,
        min_detection_confidence=MP_DETECTION_CONF,
    )

    # ── Process all files ──────────────────────────────────────────────────────
    all_new_rows: list[list] = []
    gesture_stats: dict[str, dict] = {}  # label → {"video": N, "image": N}
    t_start = time.time()

    total = len(file_list)
    for i, (label, path, kind) in enumerate(file_list, 1):
        print(f"\n[{i}/{total}] Gesture : {label}  |  Type : {kind.upper()}")
        print(f"          File    : {path.name}")

        if kind == "image":
            new_rows = _process_image(path, label, hands_static, target_cols)
            print(f"    Rows extracted   : {len(new_rows):>5}  "
                  f"({'hand found' if new_rows else 'no hand detected'})")
        else:
            new_rows = _process_video(path, label, hands_video, target_cols)

        all_new_rows.extend(new_rows)

        # Per-gesture stats tracking
        if label not in gesture_stats:
            gesture_stats[label] = {"video": 0, "image": 0}
        gesture_stats[label][kind] += len(new_rows)

    hands_static.close()
    hands_video.close()

    # ── Summary ────────────────────────────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'─' * 62}")
    print(f"  Extraction complete in {elapsed:.1f}s")
    print(f"  Total new rows     : {len(all_new_rows)}")
    print(f"\n  Per-gesture breakdown:")
    print(f"  {'Gesture':<24} {'Images':>8} {'Video':>8} {'Total':>8}")
    print(f"  {'─'*24} {'─'*8} {'─'*8} {'─'*8}")
    for lbl in sorted(gesture_stats):
        s     = gesture_stats[lbl]
        total_rows = s["image"] + s["video"]
        bar   = "▓" * (total_rows // 20)
        print(f"  {lbl:<24} {s['image']:>8} {s['video']:>8} {total_rows:>8}  {bar}")

    if not all_new_rows:
        print("\n[Extractor] ⚠  No rows extracted. Check that hands are visible.")
        sys.exit(0)

    # ── Append & save ──────────────────────────────────────────────────────────
    header   = _build_header(target_cols)
    new_df   = pd.DataFrame(all_new_rows, columns=header)
    combined = pd.concat([existing_df, new_df], ignore_index=True)

    DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(DATASET_CSV, index=False)

    print(f"\n[Extractor] ✓ Dataset saved → {DATASET_CSV}")
    print(f"             Rows before   : {existing_len}")
    print(f"             Rows added    : {len(all_new_rows)}")
    print(f"             Rows after    : {len(combined)}")
    print(f"\n             Run  python scripts/train_model.py  to retrain.\n")


if __name__ == "__main__":
    main()