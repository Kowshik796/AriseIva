"""
arise-iva | Landmark Processor — Single & Dual Hand Support
============================================================
Converts raw MediaPipe hand landmarks into normalised feature vectors.

Single-hand vector : 42 floats  (21 landmarks × [x, y])
Dual-hand vector   : 84 floats  (left_42 + right_42)

When only one hand is present in dual mode, the missing hand's 42 values
are filled with zeros so the vector length is always constant — this is
required for a fixed-size ML model input.

Normalisation strategy (per hand)
----------------------------------
  1. Translate all 21 landmarks so the wrist (index 0) is at the origin.
  2. Divide by the maximum absolute coordinate → range [-1, 1].
  This makes each hand's vector invariant to position and rough scale.
"""

from __future__ import annotations
from typing import Optional
import numpy as np


# Canonical zero vector used to pad a missing hand (42 zeros)
_EMPTY_HAND = [0.0] * 42


class LandmarkProcessor:
    """
    Extracts and normalises MediaPipe hand landmarks into ML-ready vectors.

    Usage — single hand (original behaviour)::

        processor = LandmarkProcessor()
        vector = processor.extract_landmarks(results)       # 42 floats | None

    Usage — dual hand::

        vector = processor.extract_dual_landmarks(results)  # always 84 floats
    """

    NUM_LANDMARKS = 21
    SINGLE_VECTOR_LEN = NUM_LANDMARKS * 2   # 42
    DUAL_VECTOR_LEN   = SINGLE_VECTOR_LEN * 2  # 84

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract_landmarks(self, results) -> Optional[list[float]]:
        """
        Extract landmarks from the FIRST detected hand only.

        Returns:
            42-float normalised vector, or None if no hand detected.
        """
        if not results or not results.multi_hand_landmarks:
            return None
        return self._normalise(results.multi_hand_landmarks[0])

    def extract_dual_landmarks(self, results) -> Optional[list[float]]:
        """
        Extract landmarks for BOTH hands and return an 84-float vector.

        Hand assignment
        ---------------
        MediaPipe labels each detected hand as "Left" or "Right" via
        ``results.multi_handedness``.  We always place the left hand's
        42 values first, then the right hand's 42 values.  If a hand is
        absent its slot is filled with 42 zeros.

        Returns:
            84-float vector (left_42 + right_42).
            Returns None if NO hands are detected at all.
        """
        if not results or not results.multi_hand_landmarks:
            return None

        left_vec  = list(_EMPTY_HAND)   # 42 zeros — overwritten if hand present
        right_vec = list(_EMPTY_HAND)

        for hand_lm, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness,
        ):
            # MediaPipe labels are from the camera's perspective (mirrored),
            # so "Left" in MediaPipe = user's right hand in a front-facing cam.
            # We preserve MediaPipe's own labelling for consistency.
            label = handedness.classification[0].label   # "Left" or "Right"
            vec   = self._normalise(hand_lm)

            if label == "Left":
                left_vec = vec
            else:
                right_vec = vec

        return left_vec + right_vec   # 84 floats total

    def extract_all_landmarks(self, results) -> list[list[float]]:
        """Return one 42-float vector per detected hand (up to max_num_hands)."""
        if not results or not results.multi_hand_landmarks:
            return []
        return [self._normalise(lm) for lm in results.multi_hand_landmarks]

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(hand_landmarks) -> list[float]:
        """
        Wrist-translate then max-scale a single hand's 21 landmarks.

        Steps
        -----
        1. Collect raw (x, y) pairs → shape (21, 2).
        2. Subtract wrist (index 0) → origin at wrist.
        3. Divide by max(abs) → values in [-1, 1].
        4. Flatten to a 42-element Python list.
        """
        coords = np.array(
            [[lm.x, lm.y] for lm in hand_landmarks.landmark],
            dtype=np.float32,
        )
        coords -= coords[0]                        # translate to wrist origin
        max_val = np.abs(coords).max()
        if max_val > 0:
            coords /= max_val                      # normalise scale
        return [round(float(v), 6) for v in coords.flatten()]