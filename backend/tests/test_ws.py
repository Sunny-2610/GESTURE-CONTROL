from fastapi.testclient import TestClient

from app.services.control_engine import ControlEngine
from app.services.input_control import InputController, VolumeController
from app.vision.pipeline import FrameSnapshot


def test_ws_sends_frame_and_state(app):
    with TestClient(app) as client:
        with client.websocket_connect("/ws/gestures") as ws:
            message = ws.receive_json()
            assert message["type"] == "frame"
            assert message["state"] == "OFF"
            assert message["hands"] == []


def test_ws_frame_carries_engine_fields(app):
    """Frame messages expose mode/volume/dwell/toast from the control engine."""
    rt = app.state.runtime
    pipeline = FrameSnapshot.__new__(FrameSnapshot)  # minimal fake pipeline
    pipeline.snapshot = FrameSnapshot()
    pipeline.input_ctl = InputController(dry_run=True)
    pipeline.engine = ControlEngine(
        pipeline.input_ctl,
        VolumeController(dry_run=True),
        lambda event, detail: None,
        clock=lambda: 1000.0,
    )
    pipeline.engine._active_gesture = "three_finger"
    pipeline.stop = lambda: None
    pipeline.engine.volume.set_percent(42.0)
    rt.pipeline = pipeline
    try:
        with TestClient(app) as client:
            with client.websocket_connect("/ws/gestures") as ws:
                frame = ws.receive_json()
        assert frame["mode"] == "volume"
        assert frame["volume"] == 42.0
        assert frame["volume_direction"] == 0
        assert frame["scroll_velocity"] == 0.0
        assert frame["dwell_progress"] == 0.0
        assert frame["toast"] is None
    finally:
        rt.pipeline = None


def test_ws_frame_toast_from_engine(app):
    rt = app.state.runtime
    pipeline = FrameSnapshot.__new__(FrameSnapshot)
    pipeline.snapshot = FrameSnapshot()
    pipeline.input_ctl = InputController(dry_run=True)
    pipeline.engine = ControlEngine(
        pipeline.input_ctl,
        VolumeController(dry_run=True),
        lambda event, detail: None,
        clock=lambda: 1000.0,
    )
    pipeline.engine._toast = {"text": "Click", "ts": 1000.0}
    rt.pipeline = pipeline
    pipeline.stop = lambda: None
    try:
        with TestClient(app) as client:
            with client.websocket_connect("/ws/gestures") as ws:
                frame = ws.receive_json()
        assert frame["toast"] == {"text": "Click", "ts": 1000.0}
    finally:
        rt.pipeline = None


def test_input_mode_roundtrip_for_tutorial(app):
    """Tutorial flow: force dry-run, then restore the previous mode."""
    with TestClient(app) as client:
        # tutorial starts from live input and forces preview
        assert client.post("/api/input-mode", json={"live": True}).json()["live"] is True
        assert client.get("/api/status").json()["input_live"] is True
        assert client.post("/api/input-mode", json={"live": False}).json()["live"] is False
        # ... and restores live on unmount
        assert client.post("/api/input-mode", json={"live": True}).json()["live"] is True
        assert client.get("/api/status").json()["input_live"] is True
        # restore must not swallow errors even if called twice (idempotent)
        assert client.post("/api/input-mode", json={"live": False}).json()["live"] is False



def test_ws_closing_disables_control(app):
    app.state.runtime.settings_store.update(
        {"safety": {"auto_disable_on_disconnect": True}}
    )
    app.state.runtime.settings_store.save()
    rt = app.state.runtime
    with TestClient(app) as client:
        client.post(
            "/api/controller/start",
            json={"checks": {"hand_visible": True, "nothing_unsaved": True, "emergency_shortcut": True}},
        )
        assert rt.machine.state.value == "ACTIVE"
        with client.websocket_connect("/ws/gestures") as ws:
            ws.receive_json()
        # after disconnect, control must be disabled automatically
        assert rt.machine.state.value == "OFF"
        events = [e.event for e in rt.machine.log]
        assert "CONTROL DISABLED" in events


def test_ws_disconnect_keep_control_when_disabled_setting(app):
    app.state.runtime.settings_store.update(
        {"safety": {"auto_disable_on_disconnect": False}}
    )
    app.state.runtime.settings_store.save()
    rt = app.state.runtime
    with TestClient(app) as client:
        client.post(
            "/api/controller/start",
            json={"checks": {"hand_visible": True, "nothing_unsaved": True, "emergency_shortcut": True}},
        )
        with client.websocket_connect("/ws/gestures") as ws:
            ws.receive_json()
        assert rt.machine.state.value == "ACTIVE"
