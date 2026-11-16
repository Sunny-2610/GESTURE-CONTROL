import time

import pytest

from app.schemas.models import AppSettings
from app.services.control_engine import ControlEngine
from app.services.input_control import InputController, VolumeController
from app.vision.pipeline import VisionPipeline


@pytest.fixture()
def engine():
    return ControlEngine(InputController(dry_run=True), VolumeController(dry_run=True), lambda e, d: None)


def hand_landmarks(index_tip=(0.5, 0.5)):
    lm = [[0.5, 0.9, 0.0]] * 21
    lm[5] = [0.5, index_tip[1], 0.0]
    lm[8] = [index_tip[0], index_tip[1], 0.0]
    lm[12] = [index_tip[0] + 0.02, index_tip[1], 0.0]
    return lm


def test_pointer_moves_cursor(engine):
    settings = AppSettings()
    # acquisition frame
    engine.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)
    assert engine.input.last_xy is None
    engine.dispatch("pointer", hand_landmarks((0.6, 0.5)), 0.5, settings)
    assert engine.input.last_xy is not None
    x1, _ = engine.input.last_xy
    # dx is negated for the unmirrored frame: image x growing rightwards means
    # the hand drifted left in real space, so the cursor must move left
    assert x1 < 960


def test_pinch_click_fires_once_with_cooldown(engine):
    settings = AppSettings()
    clicks = []

    original = engine.input.click

    def spy(double=False):
        clicks.append(double)
        original(double)

    engine.input.click = spy
    engine.dispatch("pinch_click", hand_landmarks(), 0.02, settings)
    assert clicks == [False]
    # still pinching -> no new click
    engine.dispatch("pinch_click", hand_landmarks(), 0.02, settings)
    assert clicks == [False]
    # release then pinch again within cooldown -> still no new click
    engine.dispatch("pointer", hand_landmarks(), 0.5, settings)
    engine.dispatch("pinch_click", hand_landmarks(), 0.02, settings)
    assert clicks == [False]


def test_scroll_dispatch(engine):
    settings = AppSettings()
    scrolls = []
    original = engine.input.scroll
    engine.input.scroll = lambda amount: scrolls.append(amount)
    engine.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.5)), 0.5, settings)
    engine.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.6)), 0.5, settings)
    assert scrolls and scrolls[0] < 0  # hand down -> scroll negative (down)


def test_reset_clears_baselines(engine):
    settings = AppSettings()
    engine.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)
    engine.reset()
    assert engine._cursor_prev is None and engine._smoothed is None


def test_volume_dry_run(engine):
    settings = AppSettings()
    before = engine.volume.get_percent()
    engine.dispatch("volume_mode", hand_landmarks((0.5, 0.5)), 0.5, settings)
    engine.dispatch("volume_mode", hand_landmarks((0.5, 0.4)), 0.5, settings)  # hand up
    after = engine.volume.get_percent()
    assert after > before


def test_auto_disable_ignores_stale_hand_timestamp():
    from app.state.machine import ControllerMachine

    machine = ControllerMachine()
    pipeline = VisionPipeline(
        machine=machine,
        settings_store=_FakeStore(),
        input_ctl=InputController(dry_run=True),
        volume_ctl=VolumeController(dry_run=True),
        emit=lambda e, d: None,
    )
    pipeline._last_hand_seen = time.time() - 60.0
    machine.arm()
    machine.activate()
    pipeline._check_auto_disable(time.time())
    assert machine.state.value == "ACTIVE"

    pipeline._last_hand_seen = time.time()
    pipeline._check_auto_disable(pipeline._last_hand_seen + 6.0)
    assert machine.state.value == "HOLD"
    assert pipeline._auto_hold is True


def test_auto_hold_resumes_when_the_hand_returns():
    from app.state.machine import ControllerMachine

    machine = ControllerMachine()
    pipeline = VisionPipeline(
        machine=machine,
        settings_store=_FakeStore(),
        input_ctl=InputController(dry_run=True),
        volume_ctl=VolumeController(dry_run=True),
        emit=lambda e, d: None,
    )
    machine.arm()
    machine.activate()
    pipeline._last_hand_seen = time.time()
    pipeline._check_auto_disable(pipeline._last_hand_seen + 6.0)
    assert machine.state.value == "HOLD"

    pipeline._resume_on_hand()
    assert machine.state.value == "ACTIVE"
    assert pipeline._auto_hold is False


def test_single_hand_dispatches_even_when_role_is_secondary():
    from app.state.machine import ControllerMachine

    machine = ControllerMachine()
    pipeline = VisionPipeline(
        machine=machine,
        settings_store=_FakeStore(),
        input_ctl=InputController(dry_run=True),
        volume_ctl=VolumeController(dry_run=True),
        emit=lambda e, d: None,
    )
    hand = {
        "hand": "Left",
        "role": "secondary",
        "confidence": 0.95,
        "gesture": "pointer",
        "landmarks": hand_landmarks((0.5, 0.5)),
        "finger_states": [False, True, False, False, False],
        "pinch": 0.5,
    }
    machine.arm()
    machine.activate()
    for _ in range(3):
        pipeline._handle_control(hand, 1)
    pipeline._handle_control({**hand, "landmarks": hand_landmarks((0.6, 0.5))}, 1)
    assert pipeline.input_ctl.last_xy is not None


def test_gesture_flicker_is_ignored():
    from app.state.machine import ControllerMachine

    machine = ControllerMachine()
    pipeline = VisionPipeline(
        machine=machine,
        settings_store=_FakeStore(),
        input_ctl=InputController(dry_run=True),
        volume_ctl=VolumeController(dry_run=True),
        emit=lambda e, d: None,
    )
    hand = {
        "hand": "Right",
        "role": "primary",
        "confidence": 0.95,
        "gesture": "pointer",
        "landmarks": hand_landmarks((0.5, 0.5)),
        "finger_states": [False, True, False, False, False],
        "pinch": 0.5,
    }
    machine.arm()
    machine.activate()
    for _ in range(3):
        pipeline._handle_control(hand)
    assert pipeline._stable_gesture == "pointer"
    pipeline._handle_control({**hand, "gesture": "pinch_click", "pinch": 0.01})
    assert pipeline._stable_gesture == "pointer"
    for _ in range(2):
        pipeline._handle_control({**hand, "gesture": "pinch_click", "pinch": 0.01})
    assert pipeline._stable_gesture == "pinch_click"


def test_pipeline_dispatches_only_when_active():
    from app.state.machine import ControllerMachine

    events = []
    machine = ControllerMachine()
    pipeline = VisionPipeline(
        machine=machine,
        settings_store=_FakeStore(),
        input_ctl=InputController(dry_run=True),
        volume_ctl=VolumeController(dry_run=True),
        emit=lambda e, d: events.append(e),
    )
    hand = {
        "hand": "Right",
        "role": "primary",
        "confidence": 0.95,
        "gesture": "pointer",
        "landmarks": hand_landmarks((0.5, 0.5)),
        "finger_states": [False, True, False, False, False],
        "pinch": 0.5,
    }
    pipeline._handle_control(hand)  # OFF: no cursor change
    assert pipeline.input_ctl.last_xy is None
    machine.arm()
    machine.activate()
    for _ in range(3):
        pipeline._handle_control(hand)  # ACTIVE: acquisition, still no move
    pipeline._handle_control({**hand, "landmarks": hand_landmarks((0.6, 0.5))})
    assert pipeline.input_ctl.last_xy is not None
    assert events  # gesture-change events logged


def test_handedness_label_swap_makes_control_hand_primary():
    import numpy as np

    from app.state.machine import ControllerMachine

    machine = ControllerMachine()
    pipeline = VisionPipeline(
        machine=machine,
        settings_store=_FakeStore(),  # cursor.control_hand == "right"
        input_ctl=InputController(dry_run=True),
        volume_ctl=VolumeController(dry_run=True),
        emit=lambda e, d: None,
    )
    frame = np.zeros((72, 128, 3), dtype=np.uint8)
    landmarks = [[[0.5, 0.5, 0.0]] * 21]

    class _FakeCamera:
        error = None

        def read(self):
            return frame

    class _FakeLandmarker:
        # raw landmarker output: user's right hand reported as "Left"
        def detect(self, _frame, _ts):
            return landmarks, [("Left", 0.95)]

    pipeline.camera = _FakeCamera()
    pipeline.landmarker = _FakeLandmarker()
    pipeline._tick(0)
    hand = pipeline.snapshot.hands[0]
    assert hand["hand"] == "Right"  # swapped because the frame is unmirrored
    assert hand["role"] == "primary"


class _FakeStore:
    def current(self) -> AppSettings:
        return AppSettings()
