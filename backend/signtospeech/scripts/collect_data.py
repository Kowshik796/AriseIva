"""
arise-iva | Dataset Collection Script — Dual-Hand Support
==========================================================
Captures hand landmark vectors (single OR dual hand) for a named gesture
and appends them to the master CSV dataset.

Single-hand mode  →  42-float vector per row
Dual-hand mode    →  84-float vector per row (left_42 + right_42)
                      Missing hand slot is zero-padded automatically.

Folder structure
----------------
    dataset/raw_gestures/<GESTURE_NAME>/info.txt
    dataset/processed_landmarks/gesture_dataset.csv

Keyboard Controls
-----------------
    S  →  Start capturing
    P  →  Pause / resume
    Q  →  Quit (partial data is always saved)
"""

from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path

import cv2

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_SCRIPT_DIR  = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent
_APP_DIR     = _PROJECT_DIR / "app"
sys.path.insert(0, str(_APP_DIR))

from camera.camera_stream      import CameraStream        # noqa: E402
from vision.hand_detector      import HandDetector        # noqa: E402
from vision.landmark_processor import LandmarkProcessor   # noqa: E402

# ── Output paths ───────────────────────────────────────────────────────────────
RAW_GESTURES_ROOT = _PROJECT_DIR / "dataset" / "raw_gestures"
MASTER_CSV        = _PROJECT_DIR / "dataset" / "processed_landmarks" / "gesture_dataset.csv"

# ── Constants ──────────────────────────────────────────────────────────────────
DEFAULT_TARGET  = 500
MIN_FRAME_DELAY = 0.05     # ~20 samples/sec cap to keep dataset diverse

# ── HUD styling ────────────────────────────────────────────────────────────────
FONT       = cv2.FONT_HERSHEY_SIMPLEX
CLR_GREEN  = (0,  220, 140)
CLR_CYAN   = (0,  200, 255)
CLR_ORANGE = (0,  160, 255)
CLR_RED    = (0,   60, 220)
CLR_GREY   = (130, 130, 130)
CLR_WHITE  = (255, 255, 255)
CLR_BAR_BG = (40,  40,  40)


# ══════════════════════════════════════════════════════════════════════════════
# CSV helpers
# ══════════════════════════════════════════════════════════════════════════════

def _build_header(dual: bool) -> list[str]:
    """
    Build CSV header for single (42 coords) or dual (84 coords) mode.
    Dual header: label, Lx0,Ly0,…,Lx20,Ly20, Rx0,Ry0,…,Rx20,Ry20
    """
    cols = ["label"]
    prefix = ["L", "R"] if dual else [""]
    for p in prefix:
        for i in range(21):
            cols += [f"{p}x{i}", f"{p}y{i}"]
    return cols


def _ensure_csv(path: Path, dual: bool) -> None:
    """Create the CSV with appropriate header if it doesn't yet exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(_build_header(dual))
        print(f"[Collector] Created CSV ({'dual' if dual else 'single'}-hand): {path}")
    else:
        print(f"[Collector] Appending to: {path}")


def _append_row(path: Path, label: str, vector: list[float]) -> None:
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow([label] + vector)


# ══════════════════════════════════════════════════════════════════════════════
# Gesture folder
# ══════════════════════════════════════════════════════════════════════════════

def _setup_folder(gesture_name: str, dual: bool) -> Path:
    folder = RAW_GESTURES_ROOT / gesture_name.upper()
    folder.mkdir(parents=True, exist_ok=True)
    meta = folder / "info.txt"
    mode = "dual-hand" if dual else "single-hand"
    if not meta.exists():
        with open(meta, "w") as f:
            f.write(f"Gesture : {gesture_name.upper()}\n")
            f.write(f"Mode    : {mode}\n")
            f.write(f"Created : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"[Collector] Folder: {folder}  mode={mode}")
    return folder


def _write_session_log(folder: Path, collected: int, target: int) -> None:
    try:
        with open(folder / "info.txt", "a") as f:
            f.write(f"\nSession : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Samples : {collected} / {target}\n")
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# HUD
# ══════════════════════════════════════════════════════════════════════════════

def _draw_hud(
    frame,
    gesture: str,
    collected: int,
    target: int,
    state: str,
    hand_count: int,
    dual_mode: bool,
    fps: float,
) -> None:
    h, w = frame.shape[:2]

    # Top banner background
    ov = frame.copy()
    cv2.rectangle(ov, (0, 0), (w, 110), (0, 0, 0), -1)
    cv2.addWeighted(ov, 0.50, frame, 0.50, 0, frame)

    state_col = CLR_GREEN if state == "CAPTURING" else (CLR_ORANGE if state == "PAUSED" else CLR_CYAN)

    # Mode badge
    mode_txt = "DUAL-HAND" if dual_mode else "SINGLE-HAND"
    mode_col = CLR_ORANGE if dual_mode else CLR_CYAN
    cv2.putText(frame, mode_txt, (w - 145, 20), FONT, 0.52, mode_col, 1, cv2.LINE_AA)

    # Row 1 — gesture name
    cv2.putText(frame, f"Gesture : {gesture}",
                (14, 30), FONT, 0.80, state_col, 2, cv2.LINE_AA)

    # Row 2 — sample counter
    cv2.putText(frame, f"Samples : {collected} / {target}",
                (14, 62), FONT, 0.75, CLR_WHITE, 2, cv2.LINE_AA)

    # Progress bar
    bar_w = w - 28
    filled = int(bar_w * (collected / target)) if target else 0
    cv2.rectangle(frame, (14, 72), (14 + bar_w, 86), CLR_BAR_BG, -1)
    cv2.rectangle(frame, (14, 72), (14 + filled,  86), state_col, -1)

    # FPS
    cv2.putText(frame, f"{fps:.0f}fps", (w - 68, 60), FONT, 0.48, CLR_GREY, 1, cv2.LINE_AA)

    # State badge
    if state == "CAPTURING":
        dot = CLR_GREEN if int(time.time() * 2) % 2 == 0 else (0, 100, 50)
        cv2.circle(frame, (w - 18, 100), 8, dot, -1)
        cv2.putText(frame, "REC", (w - 62, 105), FONT, 0.52, CLR_GREEN, 2, cv2.LINE_AA)
    elif state == "PAUSED":
        cv2.putText(frame, "PAUSED", (w - 90, 105), FONT, 0.52, CLR_ORANGE, 2, cv2.LINE_AA)
    else:
        cv2.putText(frame, "READY", (w - 78, 105), FONT, 0.52, CLR_CYAN, 2, cv2.LINE_AA)

    # Hand count indicator (dual mode shows 0/1/2)
    if dual_mode:
        hand_txt = f"Hands: {hand_count}/2"
        hcol = CLR_GREEN if hand_count == 2 else (CLR_ORANGE if hand_count == 1 else CLR_RED)
        cv2.putText(frame, hand_txt, (14, 105), FONT, 0.58, hcol, 1, cv2.LINE_AA)

    # Warning if not enough hands for mode
    required = 2 if dual_mode else 1
    if hand_count < required:
        ov2 = frame.copy()
        cv2.rectangle(ov2, (0, h - 56), (w, h - 30), (0, 0, 0), -1)
        cv2.addWeighted(ov2, 0.50, frame, 0.50, 0, frame)
        warn = (f"Show BOTH hands for dual-hand capture  ({hand_count}/2 detected)"
                if dual_mode else "No hand detected — waiting...")
        cv2.putText(frame, warn, (14, h - 36), FONT, 0.58, CLR_RED, 2, cv2.LINE_AA)

    # Key hints
    ov3 = frame.copy()
    cv2.rectangle(ov3, (0, h - 28), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(ov3, 0.55, frame, 0.45, 0, frame)
    hints = "[S] Start    [P] Pause    [Q] Quit"
    tw = cv2.getTextSize(hints, FONT, 0.50, 1)[0][0]
    cv2.putText(frame, hints, ((w - tw) // 2, h - 9), FONT, 0.50, CLR_GREY, 1, cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n" + "=" * 58)
    print("   Arise IVA  —  Dataset Collector  (Dual-Hand Support)")
    print("=" * 58)

    # ── User prompts ───────────────────────────────────────────────────────────
    gesture_name = input("\n  Gesture name (e.g. PLEASE): ").strip().upper()
    if not gesture_name:
        print("[Collector] No name entered. Exiting.")
        sys.exit(1)

    mode_input = input("  Hand mode — [1] Single  [2] Dual (default 1): ").strip()
    dual_mode  = mode_input == "2"

    raw_target = input(f"  Samples to collect [default {DEFAULT_TARGET}]: ").strip()
    target = int(raw_target) if raw_target.isdigit() and int(raw_target) > 0 else DEFAULT_TARGET

    print(f"\n  Gesture : {gesture_name}")
    print(f"  Mode    : {'Dual-hand (84 features)' if dual_mode else 'Single-hand (42 features)'}")
    print(f"  Target  : {target} samples")
    print(f"  CSV     : {MASTER_CSV}")
    print("\n  [S] Start    [P] Pause    [Q] Quit\n")

    # ── Setup ──────────────────────────────────────────────────────────────────
    gesture_folder = _setup_folder(gesture_name, dual_mode)
    _ensure_csv(MASTER_CSV, dual_mode)

    try:
        stream = CameraStream(camera_index=0)
    except RuntimeError as exc:
        print(f"[Collector] Camera error: {exc}")
        sys.exit(1)

    # Always initialise with max_hands=2 so MediaPipe sees both hands
    detector  = HandDetector(max_hands=2, detection_confidence=0.7)
    processor = LandmarkProcessor()

    # ── State ──────────────────────────────────────────────────────────────────
    collected      = 0
    state          = "READY"
    last_save_time = 0.0
    fps_counter    = 0
    fps_timer      = time.time()
    fps            = 0.0

    win_title = f"Arise IVA — Collecting: {gesture_name} ({'Dual' if dual_mode else 'Single'})"

    # ── Capture loop ───────────────────────────────────────────────────────────
    try:
        while collected < target:
            ret, frame = stream.cap.read()
            if not ret:
                print("[Collector] Frame read failed.")
                break

            now = time.time()
            fps_counter += 1
            if now - fps_timer >= 1.0:
                fps = fps_counter / (now - fps_timer)
                fps_counter = 0
                fps_timer   = now

            # MediaPipe detection
            import mediapipe as mp
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = detector.hands.process(rgb)
            rgb.flags.writeable = True

            # Draw landmarks
            frame = detector.detect_hands(frame)

            # Count detected hands
            hand_count = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0

            # Extract the appropriate feature vector
            if dual_mode:
                # Dual mode: always 84 floats; missing hand → zeros
                # Requires at least 1 hand to save (missing one is zero-padded)
                vector = processor.extract_dual_landmarks(results)
            else:
                # Single mode: 42 floats from the first detected hand
                vector = processor.extract_landmarks(results)

            hand_visible = vector is not None

            # Save sample
            # Dual mode: save even with 1 hand (other padded with zeros)
            # Single mode: need exactly 1 hand
            if (state == "CAPTURING"
                    and hand_visible
                    and (now - last_save_time) >= MIN_FRAME_DELAY):

                _append_row(MASTER_CSV, gesture_name, vector)
                collected     += 1
                last_save_time = now

                if collected % 50 == 0:
                    print(f"[Collector] {collected}/{target}  hands={hand_count}")

            # Keyboard
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == ord("Q"):
                print(f"[Collector] Quit. Saved {collected} samples.")
                break
            elif key == ord("s") or key == ord("S"):
                if state != "CAPTURING":
                    state = "CAPTURING"
                    print(f"[Collector] ▶ Started. ({collected}/{target})")
            elif key == ord("p") or key == ord("P"):
                if state == "CAPTURING":
                    state = "PAUSED"
                    print(f"[Collector] ⏸ Paused. ({collected}/{target})")
                elif state == "PAUSED":
                    state = "CAPTURING"
                    print(f"[Collector] ▶ Resumed. ({collected}/{target})")

            _draw_hud(frame, gesture_name, collected, target,
                      state, hand_count, dual_mode, fps)
            cv2.imshow(win_title, frame)

        if collected >= target:
            print(f"\n[Collector] ✓ Collected {collected}/{target} samples for '{gesture_name}'.")

    finally:
        detector.close()
        stream.cap.release()
        cv2.destroyAllWindows()
        _write_session_log(gesture_folder, collected, target)
        print(f"[Collector] Saved → {MASTER_CSV}")


if __name__ == "__main__":
    main()