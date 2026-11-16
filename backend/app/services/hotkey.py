"""Global emergency hotkey (CTRL+ALT+SHIFT+Q) via Win32 RegisterHotKey."""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import threading
from typing import Callable, Optional

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
WM_HOTKEY = 0x0312


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.wintypes.HWND),
        ("message", ctypes.wintypes.UINT),
        ("wParam", ctypes.wintypes.WPARAM),
        ("lParam", ctypes.wintypes.LPARAM),
        ("time", ctypes.wintypes.DWORD),
        ("pt", ctypes.wintypes.POINT),
    ]


class EmergencyHotkey:
    """Registers the hotkey for a background message loop; callback runs on that thread."""

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self.registered = False
        self._registered_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._thread_id: int = 0

    def start(self) -> bool:
        self._thread = threading.Thread(target=self._run, name="emergency-hotkey", daemon=True)
        self._thread.start()
        return True

    def wait_registered(self, timeout: float = 2.0) -> bool:
        self._registered_evt.wait(timeout)
        return self.registered

    def stop(self) -> None:
        if self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT
        if self._thread is not None:
            # short join: daemon thread; Windows removes the process's keyboard
            # hook on termination anyway, so do not stall Ctrl+C for it
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        hotkey_id = 0xB00B
        ok = bool(
            user32.RegisterHotKey(None, hotkey_id, MOD_CONTROL | MOD_ALT | MOD_SHIFT, ord("Q"))
        )
        self.registered = ok
        self._registered_evt.set()
        if not ok:
            return
        msg = _MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam == hotkey_id:
                    try:
                        self.callback()
                    except Exception:
                        pass
        finally:
            user32.UnregisterHotKey(None, hotkey_id)
