from fastapi.testclient import TestClient


def test_ws_sends_frame_and_state(app):
    with TestClient(app) as client:
        with client.websocket_connect("/ws/gestures") as ws:
            message = ws.receive_json()
            assert message["type"] == "frame"
            assert message["state"] == "OFF"
            assert message["hands"] == []


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
