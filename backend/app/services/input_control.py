"""OS input dispatch (mouse, click, scroll, keys) with a dry-run default.

Live mode is opt-in; every method is a no-op unless the caller has verified
the controller is ACTIVE. Failures are reported once (de-duplicated) through
the on_error callback instead of being swallowed.
"""
from __future__ import annotations

import threading
from typing import Callable, Optional

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
    """Dispatches mouse and key actions. dry_run=True records intents without touching the OS."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run or not _PYAUTOGUI_OK
        self.available = _PYAUTOGUI_OK
        self.last_action: str = ""
        self.on_error: Optional[Callable[[str], None]] = None
        self._lock = threading.Lock()
        self._last_xy: Optional[tuple] = None
        self._error_reported = False

    @property
    def last_xy(self) -> Optional[tuple]:
        return self._last_xy

    def set_dry_run(self, dry_run: bool) -> None:
        with self._lock:
            self.dry_run = bool(dry_run) or not _PYAUTOGUI_OK

    def _report_error(self, message: str) -> None:
        """Report an input failure once per failure streak."""
        if self._error_reported:
            return
        self._error_reported = True
        self.last_action = f"input error: {message}"
        if self.on_error is not None:
            try:
                self.on_error(message)
            except Exception:
                pass

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
                if not self.dry_run:
                    try:
                        pos = pyautogui.position()
                        self._last_xy = (int(pos.x), int(pos.y))
                    except Exception:
                        self._last_xy = (size[0] // 2, size[1] // 2)
                else:
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
        """Scroll by wheel delta units (Windows: 120 units = 1 notch)."""
        with self._lock:
            self.last_action = f"scroll {amount}"
            if self.dry_run:
                return
            if amount:
                pyautogui.scroll(int(amount), _pause=False)

    def press_key(self, name: str, times: int = 1) -> None:
        """Press a named key (e.g. "volumeup", "nexttrack") one or more times."""
        with self._lock:
            self.last_action = f"key {name} x{max(1, int(times))}"
            if self.dry_run:
                return
            try:
                for _ in range(max(1, int(times))):
                    pyautogui.press(name, _pause=False)
                self._error_reported = False
            except Exception as exc:
                self._report_error(f"key {name}: {str(exc)[:80]}")

    def press_hotkey(self, *keys: str) -> None:
        """Press a key combination, e.g. press_hotkey("alt", "right")."""
        with self._lock:
            combo = "+".join(keys)
            self.last_action = f"hotkey {combo}"
            if self.dry_run:
                return
            try:
                pyautogui.hotkey(*keys, _pause=False)
                self._error_reported = False
            except Exception as exc:
                self._report_error(f"hotkey {combo}: {str(exc)[:80]}")


class VolumeController:
    """Master volume via OS media keys, tracking an ESTIMATED percent.

    Media keys give no absolute level feedback, so `percent` is only a guess:
    it starts at 50% and moves 2% per press, clamped to 0-100. The real system
    volume may differ at any time; the estimate exists purely for UI feedback.
    Nothing touches the OS in Preview (dry-run).
    """

    PERCENT_STEP = 2.0

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run or not _PYAUTOGUI_OK
        self.available = _PYAUTOGUI_OK
        self.last_action: str = ""
        self.on_error: Optional[Callable[[str], None]] = None
        self._estimated_percent = 50.0
        self._error_reported = False

    def set_dry_run(self, dry_run: bool) -> None:
        self.dry_run = bool(dry_run) or not _PYAUTOGUI_OK

    def get_percent(self) -> float:
        """ESTIMATED volume percent (see class docstring)."""
        return self._estimated_percent

    def set_percent(self, percent: float) -> float:
        """Move the estimate directly (kept for tests and manual correction)."""
        self._estimated_percent = max(0.0, min(100.0, float(percent)))
        return self._estimated_percent

    def press_key(self, name: str) -> None:
        """Send a volume media key ("volumeup" / "volumedown") to the OS."""
        if name == "volumeup":
            self._estimated_percent = min(100.0, self._estimated_percent + self.PERCENT_STEP)
        elif name == "volumedown":
            self._estimated_percent = max(0.0, self._estimated_percent - self.PERCENT_STEP)
        else:
            return
        self.last_action = f"volume {name} ~{int(self._estimated_percent)}%"
        if self.dry_run:
            return
        try:
            pyautogui.press(name, _pause=False)
            self._error_reported = False
        except Exception as exc:
            if not self._error_reported:
                self._error_reported = True
                self.last_action = f"input error: volume {name}"
                if self.on_error is not None:
                    try:
                        self.on_error(f"volume key {name}: {str(exc)[:80]}")
                    except Exception:
                        pass
