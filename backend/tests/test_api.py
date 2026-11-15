import pytest

from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("GESTURE_LIVE", raising=False)
    return create_app(start_services=False, settings_path=tmp_path / "settings.json")


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c


def test_status_shape(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    body = res.json()
    assert body["version"] == "0.1.0"
    assert body["controller"]["state"] == "OFF"
    assert body["camera"]["open"] is False
    assert set(body["checks"]) == {"camera_access", "model_loaded", "input_backend", "volume_backend"}


def test_gestures_registry(client):
    res = client.get("/api/gestures")
    assert res.status_code == 200
    gestures = res.json()["gestures"]
    assert [g["priority"] for g in gestures] == [1, 2, 3, 4, 5, 6]
    assert gestures[0]["name"] == "closed_fist"
    assert gestures[5]["name"] == "open_palm"
    assert all(g["enabled"] for g in gestures)


def test_gesture_toggle(client):
    res = client.put("/api/gestures/pointer", json={"enabled": False})
    assert res.status_code == 200
    assert res.json()["enabled"] is False
    gestures = client.get("/api/gestures").json()["gestures"]
    by_name = {g["name"]: g for g in gestures}
    assert by_name["pointer"]["enabled"] is False
    assert by_name["pinch_click"]["enabled"] is True


def test_arm_requires_all_checks(client):
    res = client.post("/api/controller/start", json={"checks": {"hand_visible": True}})
    assert res.status_code == 400
    res = client.post(
        "/api/controller/start",
        json={"checks": {"hand_visible": True, "nothing_unsaved": True, "emergency_shortcut": True}},
    )
    assert res.status_code == 200
    assert res.json()["state"] == "ACTIVE"


def test_pause_resume_stop_flow(client):
    arm(client)
    res = client.post("/api/controller/pause")
    assert res.status_code == 200
    assert res.json()["state"] == "HOLD"
    res = client.post("/api/controller/stop")
    assert res.status_code == 200
    assert res.json()["state"] == "OFF"
    # stop again fails
    assert client.post("/api/controller/stop").status_code == 409
    # pause from OFF fails
    assert client.post("/api/controller/pause").status_code == 409


def test_arm_activate_then_pause_resume(client):
    arm(client)
    # go to OFF first, then arm -> activate -> pause -> resume
    client.post("/api/controller/stop")
    arm(client)
    res = client.post("/api/controller/pause")
    assert res.status_code == 200
    assert res.json()["state"] == "HOLD"
    res = client.post("/api/controller/resume")
    assert res.status_code == 200
    assert res.json()["state"] == "ACTIVE"


def test_emergency_stop_always_available(client):
    res = client.post("/api/controller/emergency-stop")
    assert res.status_code == 200
    assert res.json()["state"] == "HALT"
    # even from HALT it stays HALT
    assert client.post("/api/controller/emergency-stop").json()["state"] == "HALT"
    # rearm resets to OFF
    assert client.post("/api/controller/rearm").json()["state"] == "OFF"


def test_stop_blocked_after_emergency(client):
    arm(client)
    client.post("/api/controller/emergency-stop")
    res = client.post("/api/controller/stop")
    assert res.status_code == 409


def test_settings_get_put(client):
    body = client.get("/api/settings").json()
    assert body["unsaved"] == 0
    res = client.put("/api/settings", json={"settings": {"cursor": {"sensitivity": 2.0}}})
    assert res.status_code == 200
    assert res.json()["settings"]["cursor"]["sensitivity"] == 2.0
    assert res.json()["unsaved"] == 0


def test_settings_validation_error(client):
    res = client.put("/api/settings", json={"settings": {"click": {"cooldown": 99}}})
    assert res.status_code == 422
    assert "click.cooldown" in res.json()["detail"]


def test_settings_reset(client):
    client.put("/api/settings", json={"settings": {"scroll": {"speed": 4.0}}})
    res = client.post("/api/settings/reset")
    assert res.json()["settings"]["scroll"]["speed"] == 1.0


def test_input_mode_defaults_to_preview(client):
    assert client.get("/api/status").json()["input_live"] is False
    assert client.get("/api/settings").json()["settings"]["input"]["mode"] == "preview"


def test_input_mode_toggle(client):
    res = client.post("/api/input-mode", json={"live": True})
    assert res.status_code == 200
    assert res.json()["live"] is True
    assert client.get("/api/status").json()["input_live"] is True
    assert client.get("/api/settings").json()["settings"]["input"]["mode"] == "live"

    res = client.post("/api/input-mode", json={"live": False})
    assert res.json()["live"] is False
    assert client.get("/api/status").json()["input_live"] is False
    assert client.get("/api/settings").json()["settings"]["input"]["mode"] == "preview"


def test_input_mode_live_blocked_while_active(client):
    arm(client)
    res = client.post("/api/input-mode", json={"live": True})
    assert res.status_code == 409
    client.post("/api/controller/stop")
    assert client.post("/api/input-mode", json={"live": True}).json()["live"] is True


def test_input_mode_persists_across_restart(app, client):
    client.post("/api/input-mode", json={"live": True})
    path = app.state.runtime.settings_store.path
    again = create_app(start_services=False, settings_path=path)
    with TestClient(again) as restarted:
        assert restarted.get("/api/status").json()["input_live"] is True


def test_events_endpoint(client):
    client.post("/api/controller/emergency-stop")
    events = client.get("/api/events").json()
    assert events[0]["event"] == "EMERGENCY STOP"
    assert all(set(e) == {"ts", "event", "detail"} for e in events)


def test_camera_off_video_conflict(client):
    res = client.get("/api/video")
    assert res.status_code == 409


def arm(client):
    res = client.post(
        "/api/controller/start",
        json={"checks": {"hand_visible": True, "nothing_unsaved": True, "emergency_shortcut": True}},
    )
    assert res.status_code == 200
    return res
