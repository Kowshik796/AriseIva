"""
arise-iva | Phase 1: Camera Stream Module
Handles webcam initialization, frame capture, and live video display.
"""

import cv2
import sys


class CameraStream:
    """
    Manages the webcam lifecycle: open → stream → release.

    Usage:
        stream = CameraStream()
        stream.start_stream()
    """

    def __init__(self, camera_index: int = 0) -> None:
        """
        Initialize the webcam.

        Args:
            camera_index: Device index for the camera (default 0 = built-in webcam).

        Raises:
            RuntimeError: If the camera cannot be opened.
        """
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Failed to open camera at index {self.camera_index}. "
                "Ensure the webcam is connected and not in use by another process."
            )

        print(f"[CameraStream] Camera {self.camera_index} initialised successfully.")

    def start_stream(self, window_title: str = "Arise IVA — Live Feed") -> None:
        """
        Begin capturing frames and display the live video feed.

        The stream runs until the user presses 'q' or the frame read fails.

        Args:
            window_title: Title shown on the OpenCV display window.
        """
        print("[CameraStream] Starting stream. Press 'q' to quit.")

        while True:
            ret, frame = self.cap.read()

            if not ret:
                print("[CameraStream] Warning: Failed to read frame. Stopping stream.")
                break

            # Overlay a minimal quit hint on the frame
            cv2.putText(
                frame,
                "Press 'q' to quit",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(window_title, frame)

            # Exit on 'q' key (waitKey returns -1 if no key pressed)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[CameraStream] 'q' pressed — exiting stream.")
                break

        self._cleanup()

    def _cleanup(self) -> None:
        """Release the camera and destroy all OpenCV windows."""
        self.cap.release()
        cv2.destroyAllWindows()
        print("[CameraStream] Resources released. Goodbye.")