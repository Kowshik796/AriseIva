"""
arise-iva | Hand Detector — Dual Hand Support
=============================================
Detects and annotates up to 2 hands using MediaPipe.
Each hand is drawn with its own colour so left/right are visually distinct.
"""

import cv2
import numpy as np
import mediapipe as mp

mp_hands  = mp.solutions.hands
mp_draw   = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

# Per-hand landmark colours: index 0 → first hand, index 1 → second hand
_HAND_COLOURS = [
    (0, 255, 180),   # teal-green  — hand 0
    (255, 140,  0),  # orange      — hand 1
]

# Custom connection style (thin white lines, colour dots override per hand)
_CONNECTION_SPEC = mp_draw.DrawingSpec(color=(200, 200, 200), thickness=1)


class HandDetector:
    """
    Wraps MediaPipe Hands for up to 2 hands.

    Usage::

        detector = HandDetector(max_hands=2)
        annotated_frame = detector.detect_hands(frame)
        results         = detector.hands.process(rgb_frame)
    """

    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence:  float = 0.5,
    ) -> None:
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._max_hands = max_hands
        print(
            f"[HandDetector] Initialised — max_hands={max_hands}, "
            f"detection={detection_confidence}, tracking={tracking_confidence}"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect_hands(self, frame: np.ndarray) -> np.ndarray:
        """
        Detect hands, draw colour-coded landmarks, return annotated frame.
        Each hand gets a different colour so left/right are easy to distinguish.
        """
        if frame is None or frame.size == 0:
            return frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)
        rgb.flags.writeable = True

        if results.multi_hand_landmarks:
            for idx, (hand_lm, handedness) in enumerate(
                zip(results.multi_hand_landmarks, results.multi_handedness)
            ):
                colour = _HAND_COLOURS[idx % len(_HAND_COLOURS)]
                label  = handedness.classification[0].label   # "Left" / "Right"

                # Draw landmarks with per-hand colour
                landmark_spec = mp_draw.DrawingSpec(
                    color=colour, thickness=2, circle_radius=3
                )
                mp_draw.draw_landmarks(
                    image=frame,
                    landmark_list=hand_lm,
                    connections=mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=landmark_spec,
                    connection_drawing_spec=_CONNECTION_SPEC,
                )

                # Label each hand above the wrist
                wrist = hand_lm.landmark[0]
                wx = int(wrist.x * frame.shape[1])
                wy = int(wrist.y * frame.shape[0]) - 14
                cv2.putText(frame, label, (wx, wy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.60, colour, 2,
                            cv2.LINE_AA)

            self._draw_hand_count(frame, len(results.multi_hand_landmarks))

        return frame

    def close(self) -> None:
        self.hands.close()
        print("[HandDetector] Resources released.")

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _draw_hand_count(frame: np.ndarray, count: int) -> None:
        cv2.putText(
            frame,
            f"Hands detected: {count}",
            (10, frame.shape[0] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65,
            (0, 255, 180), 2, cv2.LINE_AA,
        )