"""Camera capture and MediaPipe hand landmarker wrappers."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import List, Optional, Sequence

import cv2
import numpy as np

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"


class CameraDevice:
    """One cv2.VideoCapture owned and driven by the pipeline thread only."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480) -> None:
        self.index = index
        self.width = width
        self.height = height
        self._cap: Optional[cv2.VideoCapture] = None
        self._lock = threading.Lock()
        self.error: Optional[str] = None

    @property
    def open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def start(self) -> bool:
        with self._lock:
            if self.open:
                return True
            cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                self.error = "Camera unavailable or blocked by another application."
                cap.release()
                return False
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, 30)
            self._cap = cap
            self.error = None
            return True

    def stop(self) -> None:
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None

    def read(self) -> Optional[np.ndarray]:
        with self._lock:
            if self._cap is None:
                return None
            try:
                ok, frame = self._cap.read()
            except cv2.error:
                # native failure (device contention / driver hiccup): fail closed
                self.error = "Camera read failed. Device may be busy; restart the camera."
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
                return None
            if not ok:
                return None
            return frame

    def resolution(self) -> Optional[str]:
        with self._lock:
            if self._cap is None:
                return None
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return f"{w}x{h}"


class HandLandmarker:
    """MediaPipe Tasks landmarker in VIDEO mode, one hand (the control hand)."""

    def __init__(self, num_hands: int = 1) -> None:
        self.available = False
        self.error: Optional[str] = None
        self._num_hands = num_hands
        self._landmarker = None
        try:
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision

            if not MODEL_PATH.exists():
                self.error = f"model file missing: {MODEL_PATH}"
                return
            base = mp_python.BaseOptions(model_asset_path=str(MODEL_PATH))
            options = mp_vision.HandLandmarkerOptions(
                base_options=base,
                running_mode=mp_vision.RunningMode.VIDEO,
                num_hands=num_hands,
            )
            self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
            self.available = True
        except Exception as exc:  # pragma: no cover - depends on native wheel
            self.error = str(exc)

    def detect(
        self, frame_bgr: np.ndarray, ts_ms: float
    ) -> tuple[List[List[List[float]]], List[tuple[str, float]]]:
        """Returns ([hand landmarks 21x3], [(label, score), ...]) for the frame."""
        if self._landmarker is None:
            return [], []
        import mediapipe as mp

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, int(ts_ms))
        hands: List[List[List[float]]] = []
        labels: List[tuple[str, float]] = []
        for lm_list in result.hand_landmarks:
            hands.append([[p.x, p.y, p.z] for p in lm_list])
        for handed in result.handedness or []:
            if handed:
                labels.append((handed[0].category_name, float(handed[0].score)))
        return hands, labels


def encode_jpeg(frame_bgr: np.ndarray, quality: int = 80) -> Optional[bytes]:
    ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return buf.tobytes() if ok else None
