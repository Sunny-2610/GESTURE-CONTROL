"""Controller state machine, event log and a small thread-safe pub/sub hub."""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime
from typing import Callable, Deque, Dict, List, Optional

from app.schemas.models import ControllerState, EventEntry

VERSION = "0.1.0"


def now_stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


class EventHub:
    """Thread-safe publish/subscribe. Subscribers receive plain dicts."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: List[Callable[[Dict], None]] = []

    def subscribe(self, callback: Callable[[Dict], None]) -> Callable[[], None]:
        with self._lock:
            self._subs.append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._subs:
                    self._subs.remove(callback)

        return unsubscribe

    def publish(self, message: Dict) -> None:
        with self._lock:
            subs = list(self._subs)
        for sub in subs:
            try:
                sub(message)
            except Exception:  # a broken subscriber must not kill the pipeline
                pass


class ControllerMachine:
    """OFF --arm--> ARMED --activate--> ACTIVE <--> HOLD, any -> HALT, HALT -> OFF."""

    def __init__(self, hub: Optional[EventHub] = None) -> None:
        self.state = ControllerState.OFF
        self.changed_at: float = time.time()
        self.changed_stamp: str = now_stamp()
        self.hub = hub or EventHub()
        self.log: Deque[EventEntry] = deque(maxlen=50)
        self._lock = threading.RLock()

    # -- logging ---------------------------------------------------------

    def emit(self, event: str, detail: str = "") -> None:
        entry = EventEntry(ts=now_stamp(), event=event, detail=detail)
        with self._lock:
            self.log.appendleft(entry)
        self.hub.publish({"type": "event", "entry": entry.model_dump(mode="json")})

    # -- transitions -----------------------------------------------------

    def _set(self, new_state: ControllerState) -> None:
        self.state = new_state
        self.changed_at = time.time()
        self.changed_stamp = now_stamp()
        self.hub.publish({"type": "state", "state": new_state.value})

    def arm(self) -> None:
        with self._lock:
            if self.state is not ControllerState.OFF:
                raise InvalidTransition(f"cannot arm from {self.state.value}")
            self._set(ControllerState.ARMED)
            self.emit("CONTROL ARMED")

    def activate(self) -> None:
        with self._lock:
            if self.state is not ControllerState.ARMED:
                raise InvalidTransition(f"cannot activate from {self.state.value}")
            self._set(ControllerState.ACTIVE)
            self.emit("CONTROL ACTIVE")

    def pause(self) -> None:
        with self._lock:
            if self.state is not ControllerState.ACTIVE:
                raise InvalidTransition(f"cannot pause from {self.state.value}")
            self._set(ControllerState.HOLD)
            self.emit("CONTROL HOLD")

    def resume(self) -> None:
        with self._lock:
            if self.state is not ControllerState.HOLD:
                raise InvalidTransition(f"cannot resume from {self.state.value}")
            self._set(ControllerState.ACTIVE)
            self.emit("CONTROL RESUMED")

    def stop(self, reason: str = "") -> None:
        with self._lock:
            if self.state is ControllerState.OFF:
                raise InvalidTransition("control already off")
            if self.state is ControllerState.HALT:
                raise InvalidTransition("control halted; use re-arm")
            self._set(ControllerState.OFF)
            self.emit("CONTROL STOPPED", reason)

    def emergency_stop(self, source: str = "UI") -> None:
        with self._lock:
            previous = self.state
            if previous is not ControllerState.OFF:
                self.emit("CONTROL HALTED", f"from {previous.value}")
            self._set(ControllerState.HALT)
            self.emit("EMERGENCY STOP", source)

    def rearm(self) -> None:
        with self._lock:
            if self.state is not ControllerState.HALT:
                raise InvalidTransition("re-arm only after emergency stop")
            self._set(ControllerState.OFF)
            self.emit("RE-ARM COMPLETE", "control off")

    # -- helpers ---------------------------------------------------------

    def is_live(self) -> bool:
        return self.state is ControllerState.ACTIVE

    def snapshot(self) -> Dict:
        with self._lock:
            return {
                "state": self.state,
                "changed_at": self.changed_at,
                "since": self.changed_stamp,
            }


class InvalidTransition(Exception):
    pass
