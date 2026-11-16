"""Turns classified hand observations into OS input, gated by the caller on ACTIVE.

All time-based logic runs on an injectable monotonic clock so tests can
simulate elapsed time deterministically.
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional, Sequence

from app.schemas.models import AppSettings
from app.services.input_control import InputController, VolumeController

EMIT = Callable[[str, str], None]  # (event, detail)
Clock = Callable[[], float]

WHEEL_DELTA = 120            # Windows wheel units per notch
SCROLL_RANGE = 0.15          # |offset| at which scrolling reaches max speed
SCROLL_MIN_RATE = 1.0        # notches/s at the dead-zone edge
SCROLL_MAX_RATE = 12.0       # notches/s at |offset| = SCROLL_RANGE
DWELL_START_RADIUS = 0.015   # normalised movement that restarts the dwell timer
DWELL_REARM_RADIUS = 0.04    # movement required before another dwell can fire
VOLUME_DEAD_ZONE = 0.03      # normalised offset below which no key is sent
VOLUME_RANGE = 0.15          # |offset| at which volume reaches max rate
VOLUME_MIN_RATE = 2.0        # presses/s at the dead-zone edge
VOLUME_MAX_RATE = 12.0       # presses/s at |offset| = VOLUME_RANGE
SWIPE_WINDOW = 0.4           # s of wrist history considered
SWIPE_TRAVEL = 0.25          # x travel inside the window required to arm
SWIPE_MIN_SPEED = 0.6        # frame widths/s
SWIPE_COOLDOWN = 1.0         # s between swipes


def _dist(a: Sequence[float], b: Sequence[float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


class ControlEngine:
    """One instance per control hand. Holds pose baselines between frames."""

    def __init__(
        self,
        input_ctl: InputController,
        volume_ctl: VolumeController,
        emit: EMIT,
        clock: Clock = time.monotonic,
    ) -> None:
        self.input = input_ctl
        self.volume = volume_ctl
        self.emit = emit
        self._clock = clock
        # surface input failures once per failure streak through the event log
        if hasattr(input_ctl, "on_error"):
            input_ctl.on_error = lambda msg: self.emit("INPUT ERROR", msg)
        if hasattr(volume_ctl, "on_error"):
            volume_ctl.on_error = lambda msg: self.emit("INPUT ERROR", msg)
        self._lock = threading.Lock()
        self._smoothed: Optional[tuple] = None      # EMA of fingertip position
        self._cursor_prev: Optional[tuple] = None   # fingertip at last cursor move
        self._pinch_down: bool = False
        self._last_click: float = 0.0
        self._active_gesture: str = "none"
        # dwell click (pointer pose)
        self._dwell_anchor: Optional[tuple] = None
        self._dwell_start: float = 0.0
        self._dwell_fired: bool = False
        self._dwell_fired_anchor: Optional[tuple] = None
        self.dwell_progress: float = 0.0
        # joystick scroll (two_finger_scroll pose)
        self._scroll_anchor: Optional[float] = None
        self._scroll_accum: float = 0.0             # fractional notches
        self._scroll_last: Optional[float] = None
        self.scroll_velocity: float = 0.0           # signed notches/s
        # volume (three_finger pose)
        self._volume_anchor: Optional[float] = None
        self._volume_accum: float = 0.0
        self._volume_last: Optional[float] = None
        self.volume_direction: int = 0               # -1 down, 0 idle, 1 up
        self._swipe_history: list = []               # [(t, wrist_x, wrist_y), ...]
        self._last_swipe: float = 0.0
        self.last_swipe: Optional[dict] = None       # {"dir": "left"|"right", "ts": t}
        # feedback for the UI
        self._toast: Optional[dict] = None           # {"text", "ts"}
        self._paused_toast_shown: bool = False

    @property
    def volume_percent_estimate(self) -> Optional[float]:
        """ESTIMATED master volume percent (media keys give no real feedback)."""
        return self.volume.get_percent()

    def status(self) -> dict:
        """Current feedback snapshot for the websocket frame."""
        with self._lock:
            mode = {
                "none": "idle",
                "closed_fist": "paused",
                "pinch_click": "click",
                "pointer": "cursor",
                "two_finger_scroll": "scroll",
                "three_finger": "volume",
                "open_palm": "swipe",
            }.get(self._active_gesture, "idle")
            return {
                "mode": mode,
                "volume": self.volume.get_percent() if mode == "volume" else None,
                "volume_direction": self.volume_direction,
                "scroll_velocity": self.scroll_velocity,
                "dwell_progress": self.dwell_progress,
                "volume_anchor": self._volume_anchor,
                "toast": dict(self._toast) if self._toast else None,
            }

    def _set_toast(self, text: str) -> None:
        self._toast = {"text": text, "ts": self._clock()}

    def reset(self) -> None:
        """Full state reset (HOLD, stop, emergency stop)."""
        with self._lock:
            self._active_gesture = "none"
            self._smoothed = None
            self._cursor_prev = None
            self._pinch_down = False
            self._last_click = 0.0
            self._scroll_anchor = None
            self._scroll_accum = 0.0
            self._scroll_last = None
            self.scroll_velocity = 0.0
            self._volume_anchor = None
            self._volume_accum = 0.0
            self._volume_last = None
            self.volume_direction = 0
            self._dwell_anchor = None
            self._dwell_start = 0.0
            self._dwell_fired = False
            self._dwell_fired_anchor = None
            self.dwell_progress = 0.0
            self._swipe_history.clear()
            self._toast = None

    # -- per-frame dispatch ------------------------------------------------

    def dispatch(
        self,
        gesture: str,
        landmarks: Sequence[Sequence[float]],
        pinch_dist: float,
        settings: AppSettings,
    ) -> None:
        with self._lock:
            if gesture != self._active_gesture:
                self._active_gesture = gesture
                self._on_gesture_change()
            if gesture in ("closed_fist", "none"):
                self._release_baselines()
                if gesture == "closed_fist" and not self._paused_toast_shown:
                    self._set_toast("Paused")
                    self._paused_toast_shown = True
                return
            # the pinch switch is armed only while the pose is held
            if gesture != "pinch_click":
                self._pinch_down = False
            if gesture == "open_palm":
                # idle pose: keep the smoothing state but re-acquire the cursor
                # anchor on the next pointer frame so there is no jump
                self._cursor_prev = None
                self._volume_anchor = None
                if settings.swipes.enabled:
                    self._swipe_tick(landmarks)
                return
            if gesture == "pointer":
                self._pointer(landmarks, settings)
            elif gesture == "two_finger_scroll":
                self._scroll(landmarks, settings)
            elif gesture == "three_finger":
                self._volume_move(landmarks, settings)
            elif gesture == "pinch_click":
                self._pinch(pinch_dist, settings)

    # -- pose transitions ----------------------------------------------------

    def _on_gesture_change(self) -> None:
        """Clear every pose baseline; anchors are re-acquired on the new pose."""
        self._cursor_prev = None
        self._pinch_down = False
        self._scroll_anchor = None
        self._scroll_accum = 0.0
        self._scroll_last = None
        self.scroll_velocity = 0.0
        self._volume_anchor = None
        self._volume_accum = 0.0
        self._volume_last = None
        self.volume_direction = 0
        self._dwell_anchor = None
        self._dwell_start = 0.0
        self._dwell_fired = False
        self._dwell_fired_anchor = None
        self.dwell_progress = 0.0
        self._swipe_history.clear()
        self._paused_toast_shown = False

    def _release_baselines(self) -> None:
        self._cursor_prev = None
        self._scroll_anchor = None
        self._scroll_accum = 0.0
        self._scroll_last = None
        self.scroll_velocity = 0.0
        self._volume_anchor = None
        self._volume_accum = 0.0
        self._volume_last = None
        self.volume_direction = 0
        self._smoothed = None
        self._pinch_down = False

    # -- poses ---------------------------------------------------------------

    def _pointer(self, landmarks, settings: AppSettings) -> None:
        # the frame is raw/unmirrored, so track image x directly
        tip = (landmarks[8][0], landmarks[8][1])
        a = settings.cursor.smoothing
        if self._smoothed is None:
            self._smoothed = tip
        else:
            s = self._smoothed
            self._smoothed = (s[0] + (tip[0] - s[0]) * (1.0 - a), s[1] + (tip[1] - s[1]) * (1.0 - a))
        if self._cursor_prev is None:
            self._cursor_prev = self._smoothed
        else:
            sw, sh = self.input.screen_size()
            # image x grows opposite the hand's real direction (unmirrored frame):
            # moving the hand right decreases image x, so negate dx to keep the
            # cursor following the hand
            dx = -(self._smoothed[0] - self._cursor_prev[0]) * settings.cursor.sensitivity * sw
            dy = (self._smoothed[1] - self._cursor_prev[1]) * settings.cursor.sensitivity * sh
            self._cursor_prev = self._smoothed
            self.input.move_relative(dx, dy)
        self._dwell_tick(settings)

    def _dwell_tick(self, settings: AppSettings) -> None:
        """Dwell click: hold the smoothed fingertip still for dwell_ms."""
        d = settings.click
        self.dwell_progress = 0.0
        if not d.dwell_enabled:
            self._dwell_anchor = None
            self._dwell_fired = False
            return
        now = self._clock()
        pos = self._smoothed
        if self._dwell_fired:
            # one click per dwell: wait for a clear movement before re-arming
            if _dist(pos, self._dwell_fired_anchor) > DWELL_REARM_RADIUS:
                self._dwell_fired = False
                self._dwell_anchor = pos
                self._dwell_start = now
            return
        if self._dwell_anchor is None:
            self._dwell_anchor = pos
            self._dwell_start = now
            return
        if _dist(pos, self._dwell_anchor) > DWELL_START_RADIUS:
            self._dwell_anchor = pos
            self._dwell_start = now
            return
        need = max(d.dwell_ms / 1000.0, 1e-6)
        self.dwell_progress = max(0.0, min(1.0, (now - self._dwell_start) / need))
        if self.dwell_progress >= 1.0:
            self.dwell_progress = 0.0
            self._dwell_fired = True
            self._dwell_fired_anchor = pos
            self.emit("DWELL CLICK", "")
            self._set_toast("Click")
            self.input.click(double=d.double_click)

    def _pinch(self, pinch_dist: float, settings: AppSettings) -> None:
        threshold = settings.click.pinch_threshold
        now = self._clock()
        if not self._pinch_down and pinch_dist < threshold:
            self._pinch_down = True
            if now - self._last_click >= settings.click.cooldown:
                self._last_click = now
                self.emit("PINCH -> CLICK", "double" if settings.click.double_click else "")
                self._set_toast("Click")
                self.input.click(double=settings.click.double_click)
        elif self._pinch_down and pinch_dist > threshold * 1.5:
            self._pinch_down = False

    def _scroll(self, landmarks, settings: AppSettings) -> None:
        """Joystick scroll: offset from the anchor sets speed, time moves the page."""
        current_y = (landmarks[8][1] + landmarks[12][1]) / 2.0
        if self._scroll_anchor is None:
            self._scroll_anchor = current_y
            self._scroll_last = self._clock()
            self.scroll_velocity = 0.0
            return
        now = self._clock()
        dt = max(0.0, now - (self._scroll_last if self._scroll_last is not None else now))
        self._scroll_last = now
        offset = current_y - self._scroll_anchor  # hand down -> offset positive
        dead = settings.scroll.dead_zone
        over = abs(offset) - dead
        if over <= 0:
            self.scroll_velocity = 0.0
            return
        span = max(1e-6, SCROLL_RANGE - dead)
        rate = (SCROLL_MIN_RATE + (SCROLL_MAX_RATE - SCROLL_MIN_RATE) * min(1.0, over / span))
        rate *= settings.scroll.speed
        direction = -1.0 if offset > 0 else 1.0  # hand down -> scroll down (negative)
        self.scroll_velocity = direction * rate
        self._scroll_accum += rate * dt
        whole = int(self._scroll_accum)
        if whole:
            self._scroll_accum -= whole
            self.input.scroll(int(whole * WHEEL_DELTA * direction))

    def _volume_move(self, landmarks, settings: AppSettings) -> None:
        """Joystick volume: offset from the anchor sets the press rate.

        The anchor is the middle-MCP y (landmark 9) captured on entering the
        pose. Hand up (y decreasing) -> offset positive -> volumeup presses;
        hand down -> volumedown. The estimated percent lives in the volume
        controller; media keys give no absolute level.
        """
        current = landmarks[9][1]
        if self._volume_anchor is None:
            self._volume_anchor = current
            self._volume_last = self._clock()
            self.volume_direction = 0
            return
        now = self._clock()
        dt = max(0.0, now - (self._volume_last if self._volume_last is not None else now))
        self._volume_last = now
        offset = self._volume_anchor - current  # hand up -> positive
        over = abs(offset) - VOLUME_DEAD_ZONE
        if over <= 0:
            self.volume_direction = 0
            return
        span = max(1e-6, VOLUME_RANGE - VOLUME_DEAD_ZONE)
        rate = VOLUME_MIN_RATE + (VOLUME_MAX_RATE - VOLUME_MIN_RATE) * min(1.0, over / span)
        rate *= settings.volume.sensitivity
        direction = 1 if offset > 0 else -1
        self.volume_direction = direction
        self._volume_accum += rate * dt
        presses = int(self._volume_accum)
        if presses:
            self._volume_accum -= presses
            key = "volumeup" if direction > 0 else "volumedown"
            for _ in range(presses):
                self.volume.press_key(key)
            self._set_toast(f"Volume {int(round(self.volume.get_percent()))}%")

    def _swipe_tick(self, landmarks) -> None:
        """Detect horizontal swipes from a short wrist-x history (open_palm).

        The frame is raw/unmirrored: image x decreasing means the hand moves
        right, so dx < 0 -> swipe right -> alt+right (forward).
        """
        now = self._clock()
        wrist = landmarks[0]
        self._swipe_history.append((now, wrist[0], wrist[1]))
        self._swipe_history = [e for e in self._swipe_history if now - e[0] <= SWIPE_WINDOW]
        if len(self._swipe_history) < 2:
            return
        t0, x0, y0 = self._swipe_history[0]
        t1, x1, y1 = self._swipe_history[-1]
        dx = x1 - x0
        dy = y1 - y0
        dt = t1 - t0
        if dt <= 1e-6:
            return
        if abs(dx) <= SWIPE_TRAVEL:
            return
        if abs(dx) / dt <= SWIPE_MIN_SPEED:
            return
        if abs(dx) <= 2 * abs(dy):  # must be mostly horizontal
            return
        if now - self._last_swipe < SWIPE_COOLDOWN:
            return
        direction = "right" if dx < 0 else "left"
        self._last_swipe = now
        self._swipe_history.clear()  # one swipe per gesture burst
        self.last_swipe = {"dir": direction, "ts": now}
        self.emit("SWIPE RIGHT" if direction == "right" else "SWIPE LEFT",
                  "forward" if direction == "right" else "back")
        self._set_toast("Forward" if direction == "right" else "Back")
        self.input.press_hotkey("alt", "right" if direction == "right" else "left")
