"""Process-wide singletons assembled in one place (or built inert for tests)."""
from __future__ import annotations

import os
import platform
import time
from typing import Optional

from fastapi import FastAPI

from app.schemas.models import ControllerState, SystemChecks
from app.services.gestures_registry import build_registry
from app.services.input_control import InputController, VolumeController
from app.services.settings_store import SettingsStore
from app.state.machine import VERSION, ControllerMachine, EventHub
from app.vision.pipeline import VisionPipeline


class Runtime:
    def __init__(
        self,
        start_services: bool = True,
        settings_path=None,
    ) -> None:
        self.started_at: float = time.time()
        self.start_services = start_services
        self.hub = EventHub()
        self.machine = ControllerMachine(hub=self.hub)
        self.settings_store = SettingsStore(path=settings_path)
        live_input = os.environ.get("GESTURE_LIVE", "0") == "1"
        self.input_ctl = InputController(dry_run=not live_input)
        self.volume_ctl = VolumeController(dry_run=not live_input)
        self.pipeline: Optional[VisionPipeline] = None
        self.hotkey = None
        if start_services:
            from app.services.hotkey import EmergencyHotkey

            self.pipeline = VisionPipeline(
                machine=self.machine,
                settings_store=self.settings_store,
                input_ctl=self.input_ctl,
                volume_ctl=self.volume_ctl,
                emit=self.machine.emit,
            )
            self.hotkey = EmergencyHotkey(self.emergency_stop)

    # -- actions -----------------------------------------------------------

    def emergency_stop(self, source: str = "UI") -> None:
        self.machine.emergency_stop(source=source)

    # -- derived info ---------------------------------------------------------

    def system_checks(self) -> SystemChecks:
        checks = SystemChecks(
            model_loaded="OK" if (self.pipeline is None or self.pipeline.landmarker.available) else "FAIL",
            input_backend="OK" if self.input_ctl.available else "FAIL",
            volume_backend="OK" if self.volume_ctl.available or self.volume_ctl.dry_run else "FAIL",
        )
        try:
            import cv2

            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            checks.camera_access = "OK" if cap.isOpened() else "FAIL"
            cap.release()
        except Exception:
            checks.camera_access = "FAIL"
        return checks

    def system_info(self) -> dict:
        return {
            "backend": f"FastAPI {VERSION} · Python {platform.python_version()}",
            "vision": "MediaPipe Hands 0.10.21",
            "model": "hand_landmarker.task",
            "frontend": "React + TypeScript + Vite",
            "session": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.started_at)),
        }

    def gestures_payload(self) -> list:
        enabled = {
            g.name: g.enabled
            for g in build_registry(self.settings_store.current().gestures.model_dump())
        }
        return [g.model_dump(mode="json") for g in build_registry(enabled)]


def attach(app: FastAPI, runtime: Runtime) -> None:
    app.state.runtime = runtime


def get_runtime(request) -> Runtime:
    return request.app.state.runtime


def state_value(state: ControllerState) -> str:
    return state.value
