"""OS input dispatch (mouse, scroll) with a dry-run default for safety.

Live mode is opt-in through the environment variable GESTURE_LIVE=1. Every
method is a no-op unless the caller has verified the controller is ACTIVE.
"""
from __future__ import annotations

import threading
from typing import Optional

try:
    import pyautogui

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.0
    _PYAUTOGUI_OK = True
except Exception:  # pragma: no cover - headless environments
    pyautogui = None  # type: ignore[assignment]
    _PYAUTOGUI_OK = False


DEFAULT_SCREEN = (1920, 1080)


class InputController:
    """Dispatches mouse actions. dry_run=True records intents without touching the OS."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run or not _PYAUTOGUI_OK
        self.available = _PYAUTOGUI_OK
        self.last_action: str = ""
        self._lock = threading.Lock()
        self._last_xy: Optional[tuple] = None

    @property
    def last_xy(self) -> Optional[tuple]:
        return self._last_xy

    def set_dry_run(self, dry_run: bool) -> None:
        with self._lock:
            self.dry_run = bool(dry_run) or not _PYAUTOGUI_OK

    def screen_size(self) -> tuple:
        if not self.dry_run:
            try:
                size = pyautogui.size()
                return (int(size.width), int(size.height))
            except Exception:
                pass
        return DEFAULT_SCREEN

    def move_cursor(self, x: int, y: int) -> None:
        with self._lock:
            self._last_xy = (int(x), int(y))
            self.last_action = f"cursor {x},{y}"
            if self.dry_run:
                return
            pyautogui.moveTo(int(x), int(y), _pause=False)

    def move_relative(self, dx: float, dy: float) -> None:
        """Move by pixel deltas relative to the last dispatched cursor position."""
        with self._lock:
            size = self.screen_size()
            if self._last_xy is None:
                self._last_xy = (size[0] // 2, size[1] // 2)
            x = int(max(0, min(size[0] - 1, self._last_xy[0] + dx)))
            y = int(max(0, min(size[1] - 1, self._last_xy[1] + dy)))
            self._last_xy = (x, y)
            self.last_action = f"cursor {x},{y}"
            if self.dry_run:
                return
            pyautogui.moveTo(x, y, _pause=False)

    def click(self, double: bool = False) -> None:
        with self._lock:
            self.last_action = "double click" if double else "click"
            if self.dry_run:
                return
            if double:
                pyautogui.doubleClick(_pause=False)
            else:
                pyautogui.click(_pause=False)

    def scroll(self, amount: int) -> None:
        with self._lock:
            self.last_action = f"scroll {amount}"
            if self.dry_run:
                return
            if amount:
                pyautogui.scroll(int(amount), _pause=False)


class VolumeController:
    """Master output volume through pycaw; dry-run keeps a local percent."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.available = False
        self._volume = None
        self._local_percent: float = 50.0
        if not dry_run:
            self._init_backend()

    def _init_backend(self) -> None:
        try:
            from ctypes import POINTER, cast

            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            device = AudioUtilities.GetSpeakers()
            interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._volume = cast(interface, POINTER(IAudioEndpointVolume))
            self.available = True
        except Exception:  # pragma: no cover - depends on audio hardware
            self.available = False

    def set_dry_run(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        if not dry_run and self._volume is None:
            self._init_backend()

    def get_percent(self) -> float:
        if self._volume is not None:
            try:
                return round(self._volume.GetMasterVolumeLevelScalar() * 100.0, 1)
            except Exception:
                pass
        return self._local_percent

    def set_percent(self, percent: float) -> float:
        percent = max(0.0, min(100.0, percent))
        if self._volume is not None:
            try:
                self._volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
                return round(self._volume.GetMasterVolumeLevelScalar() * 100.0, 1)
            except Exception:
                pass
        self._local_percent = percent
        return percent
