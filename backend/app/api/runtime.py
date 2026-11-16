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
        live_input = self._resolve_live_input()
        self.input_ctl = InputController(dry_run=not live_input)
        self.volume_ctl = VolumeController(dry_run=not live_input)
        self.pipeline: Optional[VisionPipeline] = None
        self.hotkey = None
        self._camera_probe_ok = False
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
            self._camera_probe_ok = self._probe_camera()

    @staticmethod
    def _probe_camera() -> bool:
        """One-shot camera probe, run once at startup only.

        Opening a second cv2.VideoCapture while the vision thread owns the
        camera corrupts DirectShow state and crashes the process, so this must
        never run from a request handler.
        """
        try:
            import cv2

            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            ok = bool(cap.isOpened())
            cap.release()
            return ok
        except Exception:
            return False

    # -- actions -----------------------------------------------------------

    def _resolve_live_input(self) -> bool:
        """GESTURE_LIVE overrides the saved mode when set; otherwise use it."""
        forced = os.environ.get("GESTURE_LIVE")
        if forced is not None:
            return forced == "1"
        return self.settings_store.current().input.mode == "live"

    def set_input_live(self, live: bool) -> bool:
        """Switch between dry-run (preview) and real dispatch at runtime."""
        self.settings_store.update({"input": {"mode": "live" if live else "preview"}})
        self.settings_store.save()
        active = self.apply_input_mode()
        self.machine.emit("INPUT MODE", "live" if active else "preview")
        return active

    def apply_input_mode(self) -> bool:
        """Mirror the saved input mode onto the controllers."""
        live = self.settings_store.current().input.mode == "live"
        self.input_ctl.set_dry_run(not live)
        self.volume_ctl.set_dry_run(not live)
        return not self.input_ctl.dry_run

    def emergency_stop(self, source: str = "UI") -> None:
        self.machine.emergency_stop(source=source)

    # -- derived info ---------------------------------------------------------

    def system_checks(self) -> SystemChecks:
        cam_open = bool(self.pipeline and self.pipeline.camera.open)
        input_ok = self.input_ctl.available
        checks = SystemChecks(
            camera_access="OK" if (cam_open or self._camera_probe_ok) else "FAIL",
            model_loaded="OK" if (self.pipeline is None or self.pipeline.landmarker.available) else "FAIL",
            input_backend="OK" if input_ok else "FAIL",
            # volume now goes through the same media-key path as all input,
            # so the "volume backend" is the input backend
            volume_backend="OK" if input_ok else "FAIL",
        )
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
