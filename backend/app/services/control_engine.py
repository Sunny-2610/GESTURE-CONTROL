"""Turns classified hand observations into OS input, gated by the caller on ACTIVE."""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional, Sequence

from app.schemas.models import AppSettings
from app.services.input_control import InputController, VolumeController

EMIT = Callable[[str, str], None]  # (event, detail)


class ControlEngine:
    """One instance per control hand. Holds pose baselines between frames."""

    def __init__(
        self,
        input_ctl: InputController,
        volume_ctl: VolumeController,
        emit: EMIT,
    ) -> None:
        self.input = input_ctl
        self.volume = volume_ctl
        self.emit = emit
        self._lock = threading.Lock()
        self._smoothed: Optional[tuple] = None      # EMA of fingertip position
        self._cursor_prev: Optional[tuple] = None   # fingertip at last cursor move
        self._pinch_down: bool = False
        self._last_click: float = 0.0
        self._scroll_prev: Optional[float] = None   # fingertip y at last scroll
        self._volume_prev: Optional[float] = None
        self._volume_percent: Optional[float] = None

    def reset(self) -> None:
        with self._lock:
            self._smoothed = None
            self._cursor_prev = None
            self._pinch_down = False
            self._scroll_prev = None
            self._volume_prev = None
            self._volume_percent = None

    # -- per-frame dispatch ------------------------------------------------

    def dispatch(
        self,
        gesture: str,
        landmarks: Sequence[Sequence[float]],
        pinch_dist: float,
        settings: AppSettings,
    ) -> None:
        with self._lock:
            if gesture in ("closed_fist", "none"):
                self._release_baselines()
                return
            if gesture == "open_palm":
                # idle pose: keep the smoothing state but re-acquire the cursor
                # anchor on the next pointer frame so there is no jump
                self._scroll_prev = None
                self._volume_prev = None
                self._cursor_prev = None
                return
            if gesture == "pointer":
                self._pointer(landmarks, settings)
                self._scroll_prev = None
                self._volume_prev = None
            elif gesture == "two_finger_scroll":
                self._scroll(landmarks, settings)
                self._cursor_prev = None
                self._volume_prev = None
            elif gesture == "volume_mode":
                self._volume_move(landmarks, settings)
                self._cursor_prev = None
                self._scroll_prev = None
            elif gesture == "pinch_click":
                self._pinch(pinch_dist, settings)
                self._scroll_prev = None
                self._volume_prev = None

    # -- poses ---------------------------------------------------------------

    def _release_baselines(self) -> None:
        self._cursor_prev = None
        self._scroll_prev = None
        self._volume_prev = None
        self._smoothed = None
        self._pinch_down = False

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
            return
        sw, sh = self.input.screen_size()
        # image x grows opposite the hand's real direction (unmirrored frame):
        # moving the hand right decreases image x, so negate dx to keep the
        # cursor following the hand
        dx = -(self._smoothed[0] - self._cursor_prev[0]) * settings.cursor.sensitivity * sw
        dy = (self._smoothed[1] - self._cursor_prev[1]) * settings.cursor.sensitivity * sh
        self._cursor_prev = self._smoothed
        self.input.move_relative(dx, dy)

    def _pinch(self, pinch_dist: float, settings: AppSettings) -> None:
        threshold = settings.click.pinch_threshold
        now = time.monotonic()
        if not self._pinch_down and pinch_dist < threshold:
            self._pinch_down = True
            if now - self._last_click >= settings.click.cooldown:
                self._last_click = now
                self.emit("PINCH -> CLICK", "double" if settings.click.double_click else "")
                self.input.click(double=settings.click.double_click)
        elif self._pinch_down and pinch_dist > threshold * 1.5:
            self._pinch_down = False

    def _scroll(self, landmarks, settings: AppSettings) -> None:
        mid_y = (landmarks[8][1] + landmarks[12][1]) / 2.0
        if self._scroll_prev is None:
            self._scroll_prev = mid_y
            return
        dy = mid_y - self._scroll_prev
        self._scroll_prev = mid_y
        if abs(dy) < settings.scroll.dead_zone:
            return
        amount = int(-dy * 40.0 * settings.scroll.speed)
        if amount:
            self.input.scroll(amount)

    def _volume_move(self, landmarks, settings: AppSettings) -> None:
        anchor = landmarks[5][1]  # index MCP y
        if self._volume_prev is None:
            self._volume_prev = anchor
            if self._volume_percent is None:
                self._volume_percent = self.volume.get_percent()
            return
        dy = self._volume_prev - anchor  # moving hand up decreases y -> louder
        self._volume_prev = anchor
        if self._volume_percent is None:
            self._volume_percent = self.volume.get_percent()
        target = self._volume_percent + dy * 200.0 * settings.volume.sensitivity
        a = settings.volume.smoothing
        self._volume_percent = self._volume_percent * a + target * (1.0 - a)
        self.volume.set_percent(self._volume_percent)
