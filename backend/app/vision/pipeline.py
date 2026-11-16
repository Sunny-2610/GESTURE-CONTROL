"""Background vision loop: capture -> landmarks -> classification -> dispatch.

Publishes a snapshot (JPEG + observations) that the MJPEG route and the
WebSocket route consume. Runs actions through the ControlEngine only while
the controller state is ACTIVE.
"""
from __future__ import annotations

import threading
import queue
import time
from collections import deque
from typing import Deque, Dict, List, Optional

import numpy as np

from app.schemas.models import ControllerState
from app.services.control_engine import ControlEngine
from app.state.machine import ControllerMachine
from app.vision.capture import CameraDevice, HandLandmarker, encode_jpeg
from app.vision.classify import classify, fingers_extended, pinch_ratio

STABLE_FRAMES = 3


class FrameSnapshot:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.jpeg: Optional[bytes] = None
        self.ts: float = 0.0
        self.fps: Optional[float] = None
        self.proc_ms: Optional[float] = None
        self.hands: List[Dict] = []
        self.frame_seq: int = 0

    def update(self, **kwargs) -> None:
        with self.lock:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def copy(self) -> Dict:
        with self.lock:
            return {
                "jpeg": self.jpeg,
                "ts": self.ts,
                "fps": self.fps,
                "proc_ms": self.proc_ms,
                "hands": [dict(h) for h in self.hands],
                "frame_seq": self.frame_seq,
            }


class VisionPipeline:
    def __init__(
        self,
        machine: ControllerMachine,
        settings_store,
        input_ctl,
        volume_ctl,
        emit,
        camera_index: int = 0,
    ) -> None:
        self.machine = machine
        self.settings_store = settings_store
        self.camera = CameraDevice(camera_index)
        self.landmarker = HandLandmarker()
        self.snapshot = FrameSnapshot()
        self.emit = emit
        self.input_ctl = input_ctl
        self.volume_ctl = volume_ctl
        self.engine = ControlEngine(input_ctl, volume_ctl, emit)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._fps_hist: Deque[float] = deque(maxlen=30)
        self._last_hand_seen: float = 0.0
        self._last_gesture: str = "none"
        self._pending_gesture: str = "none"
        self._pending_count: int = 0
        self._stable_gesture: str = "none"
        self._auto_disabled: bool = False
        self._auto_hold: bool = False
        self._last_cam_error: Optional[str] = None
        self._hand_ignored_emitted: bool = False
        # all cv2.VideoCapture calls run on the vision thread via this queue
        self._cmd_q: "queue.Queue[tuple]" = queue.Queue()
        self._cmd_done = threading.Event()
        self._cmd_result: Optional[bool] = None

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="vision", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            # short join: the thread is a daemon, so the OS reclaims it on exit;
            # waiting longer only delays Ctrl+C when it is mid-inference
            self._thread.join(timeout=1.0)
            self._thread = None
        self.camera.stop()

    def start_camera(self) -> bool:
        """Open the camera on the vision thread (safe: single-threaded cv2)."""
        if self._thread is None:
            return self.camera.start()
        self._cmd_q.put(("start",))
        self._cmd_done.wait(timeout=10.0)
        self._cmd_done.clear()
        return bool(self._cmd_result)

    def stop_camera(self) -> None:
        if self._thread is None:
            self.camera.stop()
        else:
            self._cmd_q.put(("stop",))
            self._cmd_done.wait(timeout=10.0)
            self._cmd_done.clear()
        self._fps_hist.clear()
        self.snapshot.update(jpeg=None, hands=[], fps=None, proc_ms=None)
        self.emit("CAMERA STOP")

    def _drain_commands(self) -> None:
        while True:
            try:
                cmd, = self._cmd_q.get_nowait()
            except queue.Empty:
                return
            if cmd == "start":
                ok = self.camera.start()
                if ok:
                    self.emit("CAMERA START", f"cam {self.camera.index}")
                else:
                    self.emit("CAMERA ERROR", self.camera.error or "unavailable")
                self._cmd_result = ok
            elif cmd == "stop":
                self.camera.stop()
                self._cmd_result = True
            self._cmd_done.set()

    # -- main loop -------------------------------------------------------------

    def _run(self) -> None:
        interval = 1.0 / 30.0
        ts_counter = 0
        while not self._stop.is_set():
            started = time.monotonic()
            ts_counter += 33
            try:
                self._drain_commands()
                self._tick(ts_counter)
            except Exception as exc:  # keep the loop alive no matter what
                self.emit("VISION ERROR", str(exc)[:120])
                self._stop.wait(1.0)
            elapsed = time.monotonic() - started
            delay = max(0.0, interval - elapsed)
            self._stop.wait(delay)

    def _tick(self, ts_ms: int) -> None:
        proc_start = time.monotonic()
        frame = self.camera.read()
        now = time.time()
        hands: List[Dict] = []
        jpeg: Optional[bytes] = None
        if self.camera.error and self.camera.error != self._last_cam_error:
            self._last_cam_error = self.camera.error
            self.emit("CAMERA ERROR", self.camera.error)
        if frame is not None:
            lm_hands, labels = self.landmarker.detect(frame, ts_ms)
            for i, lm in enumerate(lm_hands):
                label, score = labels[i] if i < len(labels) else ("Right", 0.0)
                # MediaPipe's handedness assumes a mirrored (selfie) image, but we
                # feed it the raw unmirrored webcam frame, so the label is flipped
                # and must be swapped back for role assignment to work.
                label = "Left" if label.lower() == "right" else "Right"
                ext = fingers_extended(lm)
                gesture, _conf = classify(lm, ext)
                hands.append(
                    {
                        "hand": label,
                        "role": "primary" if label.lower() == self.settings_store.current().cursor.control_hand else "secondary",
                        "confidence": round(score, 3),
                        "gesture": gesture,
                        "landmarks": [[round(p[0], 4), round(p[1], 4), round(p[2], 4)] for p in lm],
                        "finger_states": ext,
                        "pinch": round(pinch_ratio(lm), 4),
                    }
                )
            jpeg = encode_jpeg(frame)

        fps = self._fps_measure() if frame is not None else None
        proc_ms = round((time.monotonic() - proc_start) * 1000.0, 1)
        self.snapshot.update(
            jpeg=jpeg,
            ts=now,
            fps=fps,
            proc_ms=proc_ms,
            hands=hands,
            frame_seq=self.snapshot.frame_seq + 1,
        )
        if hands:
            self._last_hand_seen = now
            self._auto_disabled = False
            self._resume_on_hand()
            self._handle_control(hands[0], len(hands))
        else:
            self._check_auto_disable(now)

    def _fps_measure(self) -> Optional[float]:
        now = time.monotonic()
        self._fps_hist.append(now)
        if len(self._fps_hist) < 10:
            return None
        span = self._fps_hist[-1] - self._fps_hist[0]
        if span < 0.3:
            return None
        return round((len(self._fps_hist) - 1) / span, 1)

    # -- control dispatch --------------------------------------------------------

    def _handle_control(self, hand: Dict, hand_count: int = 1) -> None:
        settings = self.settings_store.current()
        state = self.machine.state
        if state is ControllerState.ACTIVE:
            gesture = self._stabilize(hand["gesture"])
            if self._last_gesture != gesture:
                self.emit(gesture.upper(), f"conf {hand['confidence']:.2f}")
                self._last_gesture = gesture
            enabled = settings.gestures.model_dump()
            is_control_hand = hand["role"] == "primary" or hand_count == 1
            if not is_control_hand:
                # log once per "hand is not the control hand" stretch, not every frame
                if not self._hand_ignored_emitted:
                    self.emit("HAND IGNORED", "not control hand")
                    self._hand_ignored_emitted = True
            else:
                self._hand_ignored_emitted = False
                if enabled.get(gesture, True):
                    self.engine.dispatch(
                        gesture, hand["landmarks"], hand["pinch"], settings
                    )
        elif state is ControllerState.HOLD or state is ControllerState.ARMED:
            self._reset_gesture_stability()
            self.engine.reset()
            self._last_gesture = hand["gesture"]

    def _stabilize(self, raw: str) -> str:
        if raw == self._pending_gesture:
            self._pending_count += 1
        else:
            self._pending_gesture = raw
            self._pending_count = 1
        if raw != self._stable_gesture and self._pending_count >= STABLE_FRAMES:
            self._stable_gesture = raw
        return self._stable_gesture

    def _reset_gesture_stability(self) -> None:
        self._pending_gesture = "none"
        self._pending_count = 0
        self._stable_gesture = "none"

    def _resume_on_hand(self) -> None:
        """Bring the controller back from an automatic hold once a hand returns."""
        if not self._auto_hold or self.machine.state is not ControllerState.HOLD:
            return
        try:
            self.machine.resume()
        except Exception:
            return
        self._auto_hold = False
        self.emit("CONTROL RESUMED", "hand back in frame")

    def _check_auto_disable(self, now: float) -> None:
        settings = self.settings_store.current()
        limit = settings.safety.auto_disable_no_hand
        state = self.machine.state
        if state is not ControllerState.ACTIVE or limit <= 0:
            return
        baseline = max(self._last_hand_seen, self.machine.changed_at)
        if now - baseline > limit and not self._auto_disabled:
            self._auto_disabled = True
            self.emit("AUTO HOLD", f"no hand for {limit:.0f} s")
            try:
                self.machine.pause()
                self._auto_hold = True
            except Exception:
                pass
