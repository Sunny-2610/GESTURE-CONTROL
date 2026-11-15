import pytest

from app.schemas.models import ControllerState
from app.state.machine import ControllerMachine, InvalidTransition


@pytest.fixture()
def machine() -> ControllerMachine:
    return ControllerMachine()


def test_starts_off(machine):
    assert machine.state is ControllerState.OFF
    assert not machine.is_live()


def test_arm_activate_pause_resume(machine):
    machine.arm()
    assert machine.state is ControllerState.ARMED
    machine.activate()
    assert machine.is_live()
    machine.pause()
    assert machine.state is ControllerState.HOLD
    machine.resume()
    assert machine.is_live()


def test_stop_from_active(machine):
    machine.arm()
    machine.activate()
    machine.stop("UI")
    assert machine.state is ControllerState.OFF


def test_pause_requires_active(machine):
    with pytest.raises(InvalidTransition):
        machine.pause()


def test_resume_requires_hold(machine):
    machine.arm()
    with pytest.raises(InvalidTransition):
        machine.resume()


def test_activate_requires_armed(machine):
    with pytest.raises(InvalidTransition):
        machine.activate()


def test_stop_from_off_fails(machine):
    with pytest.raises(InvalidTransition):
        machine.stop()


def test_emergency_stop_from_any_state(machine):
    machine.emergency_stop(source="HOTKEY")
    assert machine.state is ControllerState.HALT
    machine.rearm()
    assert machine.state is ControllerState.OFF


def test_rearm_requires_halt(machine):
    with pytest.raises(InvalidTransition):
        machine.rearm()


def test_stop_blocked_while_halted(machine):
    machine.arm()
    machine.activate()
    machine.emergency_stop()
    with pytest.raises(InvalidTransition):
        machine.stop()


def test_event_log_and_hub(machine):
    seen = []
    unsubscribe = machine.hub.subscribe(seen.append)
    machine.arm()
    machine.emergency_stop("TEST")
    unsubscribe()
    assert len(seen) == 5  # arm: event+state, emergency: event+state+event
    events = [entry.event for entry in machine.log]
    assert events[0] == "EMERGENCY STOP"
    assert "CONTROL ARMED" in events
