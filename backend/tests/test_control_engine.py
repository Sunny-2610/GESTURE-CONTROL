import time

import pytest

from app.schemas.models import AppSettings
from app.services.control_engine import ControlEngine
from app.services.input_control import InputController, VolumeController
from app.vision.pipeline import VisionPipeline


def test_status_reports_mode_and_feedback():
    clock = FakeClock()
    eng = ControlEngine(
        InputController(dry_run=True),
        VolumeController(dry_run=True),
        lambda e, d: None,
        clock=clock,
    )
    settings = AppSettings()
    # default
    assert eng.status()["mode"] == "idle"
    assert eng.status()["volume"] is None
    # cursor
    eng.dispatch("pointer", hand_landmarks(), 0.5, settings)
    assert eng.status()["mode"] == "cursor"
    # click + toast
    eng.dispatch("pinch_click", hand_landmarks(), 0.02, settings)
    status = eng.status()
    assert status["mode"] == "click"
    assert status["toast"] == {"text": "Click", "ts": 1000.0}
    # volume mode
    eng.dispatch("three_finger", volume_landmarks(0.6), 0.5, settings)  # anchor
    clock.advance(0.5)
    eng.dispatch("three_finger", volume_landmarks(0.5), 0.5, settings)  # hand up
    status = eng.status()
    assert status["mode"] == "volume"
    assert status["volume"] is not None
    assert status["volume_anchor"] is not None
    assert status["toast"]["text"].startswith("Volume ")
    # paused + toast set once per entry
    clock.advance(1.0)
    eng.dispatch("closed_fist", hand_landmarks(), 0.5, settings)
    assert eng.status()["mode"] == "paused"
    assert eng.status()["toast"]["text"] == "Paused"
    paused_ts = eng.status()["toast"]["ts"]
    eng.dispatch("closed_fist", hand_landmarks(), 0.5, settings)
    assert eng.status()["toast"]["ts"] == paused_ts  # not re-freshed every frame
    # HOLD reset clears mode
    eng.reset()
    assert eng.status()["mode"] == "idle"
    assert eng.status()["toast"] is None
    # swipe toast (image x decreasing = hand moving right)
    eng.dispatch("open_palm", swipe_landmarks(0.5), 0.5, settings)
    for i in range(12):
        clock.advance(1.0 / 30.0)
        eng.dispatch("open_palm", swipe_landmarks(0.5 - i * 0.03), 0.5, settings)
    status = eng.status()
    assert status["mode"] == "swipe"
    assert status["toast"]["text"] == "Forward"


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


class FakeClock:
    def __init__(self, start=1000.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def scroll_engine():
    clicks_log = []
    ctl = InputController(dry_run=True)
    ctl.scroll = clicks_log.append
    clock = FakeClock()
    eng = ControlEngine(ctl, VolumeController(dry_run=True), lambda e, d: None, clock=clock)
    return eng, clock, clicks_log


def test_scroll_dead_zone_produces_no_scroll():
    eng, clock, scrolls = scroll_engine()
    settings = AppSettings()
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.5)), 0.5, settings)
    # drift 0.02 (inside the 0.04 dead zone), hold for 5 simulated seconds
    for _ in range(50):
        clock.advance(0.1)
        eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.52)), 0.5, settings)
    assert scrolls == []
    assert eng.scroll_velocity == 0.0


def test_scroll_is_continuous_and_time_based():
    eng, clock, scrolls = scroll_engine()
    settings = AppSettings()
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.5)), 0.5, settings)  # anchor
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.65)), 0.5, settings)  # offset 0.15
    for _ in range(20):
        clock.advance(0.1)
        eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.65)), 0.5, settings)
    assert len(scrolls) >= 5  # kept scrolling over the simulated 2 s
    assert all(s < 0 for s in scrolls)  # hand down scrolls down
    assert all(s % 120 == 0 for s in scrolls)  # whole wheel notches
    assert eng.scroll_velocity < 0


def test_scroll_anchor_resets_on_gesture_change():
    eng, clock, scrolls = scroll_engine()
    settings = AppSettings()
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.5)), 0.5, settings)
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.65)), 0.5, settings)
    clock.advance(1.0)
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.65)), 0.5, settings)
    assert scrolls  # scrolling happened
    eng.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)  # leave pose
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.65)), 0.5, settings)  # re-anchor
    before = len(scrolls)
    clock.advance(0.5)
    eng.dispatch("two_finger_scroll", hand_landmarks((0.5, 0.65)), 0.5, settings)
    # anchored again: offset 0 but time passed without an anchor change... offset
    # is 0 relative to the NEW anchor, so nothing scrolls
    assert len(scrolls) == before


def test_pinch_release_and_reclick_after_cooldown():
    clicks = []
    clock = FakeClock()
    eng = ControlEngine(InputController(dry_run=True), VolumeController(dry_run=True), lambda e, d: None, clock=clock)
    eng.input.click = lambda double=False: clicks.append(double)
    settings = AppSettings()
    eng.dispatch("pinch_click", hand_landmarks(), 0.02, settings)
    assert clicks == [False]
    # hold the pinch: still one click
    for _ in range(5):
        clock.advance(0.1)
        eng.dispatch("pinch_click", hand_landmarks(), 0.02, settings)
    assert clicks == [False]
    # release via pointer, then pinch again after the cooldown: second click
    eng.dispatch("pointer", hand_landmarks(), 0.5, settings)
    clock.advance(settings.click.cooldown + 0.1)
    eng.dispatch("pinch_click", hand_landmarks(), 0.02, settings)
    assert clicks == [False, False]


def test_dwell_click_fires_once_and_rearms():
    clicks = []
    clock = FakeClock()
    eng = ControlEngine(InputController(dry_run=True), VolumeController(dry_run=True), lambda e, d: None, clock=clock)
    eng.input.click = lambda double=False: clicks.append(double)
    settings = AppSettings()
    settings.click.dwell_enabled = True
    settings.click.dwell_ms = 1000
    # hold the fingertip still: progress climbs, then one click
    eng.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)
    clock.advance(0.5)
    eng.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)
    assert 0.0 < eng.dwell_progress < 1.0
    clock.advance(0.6)
    eng.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)
    assert clicks == [False]
    assert eng.dwell_progress == 0.0
    # tiny movement must not re-arm
    clock.advance(2.0)
    eng.dispatch("pointer", hand_landmarks((0.51, 0.5)), 0.5, settings)
    clock.advance(2.0)
    eng.dispatch("pointer", hand_landmarks((0.52, 0.5)), 0.5, settings)
    assert clicks == [False]
    # a clear movement re-arms, holding still again fires a second click
    eng.dispatch("pointer", hand_landmarks((0.58, 0.5)), 0.5, settings)  # re-arm
    eng.dispatch("pointer", hand_landmarks((0.58, 0.5)), 0.5, settings)  # smoothing settles
    clock.advance(1.1)
    eng.dispatch("pointer", hand_landmarks((0.58, 0.5)), 0.5, settings)
    assert clicks == [False, False]


def test_dwell_disabled_by_default():
    clicks = []
    clock = FakeClock()
    eng = ControlEngine(InputController(dry_run=True), VolumeController(dry_run=True), lambda e, d: None, clock=clock)
    eng.input.click = lambda double=False: clicks.append(double)
    settings = AppSettings()
    for _ in range(30):
        clock.advance(0.2)
        eng.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)
    assert clicks == []
    assert eng.dwell_progress == 0.0


def volume_engine():
    vol = VolumeController(dry_run=True)
    pressed = []
    real = vol.press_key

    def spy(name):
        pressed.append(name)
        real(name)

    vol.press_key = spy
    clock = FakeClock()
    eng = ControlEngine(InputController(dry_run=True), vol, lambda e, d: None, clock=clock)
    return eng, clock, pressed, vol


def volume_landmarks(mcp9_y):
    lm = [[0.5, 0.9, 0.0]] * 21
    lm[9] = [0.5, mcp9_y, 0.0]
    return lm


def test_volume_hand_up_sends_volumeup():
    eng, clock, pressed, vol = volume_engine()
    settings = AppSettings()
    eng.dispatch("three_finger", volume_landmarks(0.6), 0.5, settings)  # anchor
    clock.advance(0.5)
    eng.dispatch("three_finger", volume_landmarks(0.5), 0.5, settings)  # hand up
    assert pressed == ["volumeup"] * 3
    assert eng.volume_direction == 1
    assert vol.get_percent() > 50.0


def test_volume_hand_down_sends_volumedown():
    eng, clock, pressed, vol = volume_engine()
    settings = AppSettings()
    eng.dispatch("three_finger", volume_landmarks(0.6), 0.5, settings)  # anchor
    clock.advance(0.5)
    eng.dispatch("three_finger", volume_landmarks(0.7), 0.5, settings)  # hand down
    assert pressed and all(p == "volumedown" for p in pressed)
    assert eng.volume_direction == -1
    assert vol.get_percent() < 50.0


def test_volume_dead_zone_sends_nothing():
    eng, clock, pressed, vol = volume_engine()
    settings = AppSettings()
    eng.dispatch("three_finger", volume_landmarks(0.6), 0.5, settings)  # anchor
    for _ in range(50):
        clock.advance(0.1)
        eng.dispatch("three_finger", volume_landmarks(0.59), 0.5, settings)  # offset 0.01
    assert pressed == []
    assert eng.volume_direction == 0


def test_volume_rate_grows_with_offset():
    settings = AppSettings()
    eng1, clock1, pressed1, _ = volume_engine()
    eng1.dispatch("three_finger", volume_landmarks(0.6), 0.5, settings)
    clock1.advance(1.0)
    eng1.dispatch("three_finger", volume_landmarks(0.565), 0.5, settings)  # offset 0.035
    eng2, clock2, pressed2, _ = volume_engine()
    eng2.dispatch("three_finger", volume_landmarks(0.6), 0.5, settings)
    clock2.advance(1.0)
    eng2.dispatch("three_finger", volume_landmarks(0.46), 0.5, settings)  # offset 0.14
    assert len(pressed2) > len(pressed1) > 0


def test_volume_estimate_clamped_and_anchor_resets():
    eng, clock, pressed, vol = volume_engine()
    settings = AppSettings()
    eng.dispatch("three_finger", volume_landmarks(0.6), 0.5, settings)  # anchor
    for _ in range(30):
        clock.advance(0.2)
        eng.dispatch("three_finger", volume_landmarks(0.4), 0.5, settings)  # far up
    assert vol.get_percent() == 100.0  # clamped, never beyond
    # gesture change resets the anchor: first frame of the new pose re-anchors
    eng.dispatch("pointer", hand_landmarks(), 0.5, settings)
    before = len(pressed)
    eng.dispatch("three_finger", volume_landmarks(0.4), 0.5, settings)
    clock.advance(0.0)
    eng.dispatch("three_finger", volume_landmarks(0.4), 0.5, settings)
    assert len(pressed) == before  # re-anchored, no offset yet


def test_preview_never_touches_pyautogui(monkeypatch):
    import app.services.input_control as ic

    class Boom:
        def __getattr__(self, name):
            raise AssertionError("pyautogui must not be used in preview")

    monkeypatch.setattr(ic, "pyautogui", Boom())
    ctl = InputController(dry_run=True)
    ctl.press_key("volumeup")
    ctl.press_hotkey("alt", "right")
    vol = VolumeController(dry_run=True)
    vol.press_key("volumeup")
    assert ctl.last_action == "hotkey alt+right"
    assert vol.last_action.startswith("volume volumeup")
    assert vol.get_percent() == 52.0


def test_input_error_reported_once(monkeypatch):
    import app.services.input_control as ic

    class Boom:
        def __getattr__(self, name):
            raise OSError("blocked")

    monkeypatch.setattr(ic, "pyautogui", Boom())
    events = []
    eng = ControlEngine(
        InputController(dry_run=False),
        VolumeController(dry_run=False),
        lambda e, d: events.append((e, d)),
    )
    for _ in range(3):
        eng.input.press_key("a")
    assert [e for e, _ in events].count("INPUT ERROR") == 1
    eng.volume.press_key("volumeup")
    eng.volume.press_key("volumeup")
    assert [e for e, _ in events].count("INPUT ERROR") == 2  # new streak, still de-duplicated


def swipe_engine():
    hotkeys = []
    events = []
    ctl = InputController(dry_run=True)
    ctl.press_hotkey = lambda *keys: hotkeys.append(keys)
    clock = FakeClock()
    eng = ControlEngine(ctl, VolumeController(dry_run=True), lambda e, d: events.append(e), clock=clock)
    return eng, clock, hotkeys, events


def swipe_landmarks(wrist_x, wrist_y=0.5):
    lm = [[0.5, 0.9, 0.0]] * 21
    lm[0] = [wrist_x, wrist_y, 0.0]
    return lm


def run_swipe(eng, clock, hotkeys, xs, dy_per_frame=0.0, y_start=0.5):
    y = y_start
    for x in xs:
        clock.advance(1.0 / 30.0)
        y += dy_per_frame
        eng.dispatch("open_palm", swipe_landmarks(x, y), 0.5, AppSettings())
    return y


def test_swipe_right_fires_alt_right_once():
    eng, clock, hotkeys, events = swipe_engine()
    # unmirrored frame: image x decreasing = hand moving right
    run_swipe(eng, clock, hotkeys, [0.5 - i * 0.03 for i in range(12)])
    assert hotkeys == [("alt", "right")]
    assert "SWIPE RIGHT" in events
    assert eng.last_swipe["dir"] == "right"
    assert 0.0 < eng.last_swipe["ts"] <= clock.t


def test_swipe_left_fires_alt_left_once():
    eng, clock, hotkeys, events = swipe_engine()
    run_swipe(eng, clock, hotkeys, [0.2 + i * 0.03 for i in range(12)])
    assert hotkeys == [("alt", "left")]
    assert "SWIPE LEFT" in events


def test_swipe_cooldown_blocks_immediate_second():
    eng, clock, hotkeys, _ = swipe_engine()
    run_swipe(eng, clock, hotkeys, [0.5 - i * 0.03 for i in range(12)])
    assert hotkeys == [("alt", "right")]
    # keep swiping right after the burst: inside the 1.0 s cooldown
    run_swipe(eng, clock, hotkeys, [0.2 - i * 0.03 for i in range(10)])
    assert hotkeys == [("alt", "right")]
    # after the cooldown a new burst fires again
    clock.advance(1.1)
    run_swipe(eng, clock, hotkeys, [0.5 - i * 0.03 for i in range(12)])
    assert hotkeys == [("alt", "right"), ("alt", "right")]


def test_slow_drift_does_not_swipe():
    eng, clock, hotkeys, _ = swipe_engine()
    # 0.05 frame widths per second for 2 s: travel inside any 0.4 s window is tiny
    run_swipe(eng, clock, hotkeys, [0.5 - i * 0.05 / 30.0 for i in range(60)])
    assert hotkeys == []


def test_diagonal_motion_does_not_swipe():
    eng, clock, hotkeys, _ = swipe_engine()
    run_swipe(eng, clock, hotkeys, [0.5 - i * 0.03 for i in range(12)], dy_per_frame=0.016)
    # |dx| = 0.33 but |dy| = 0.176 -> |dx| < 2|dy|: not mostly horizontal
    assert hotkeys == []


def test_leaving_open_palm_clears_swipe_history():
    eng, clock, hotkeys, _ = swipe_engine()
    run_swipe(eng, clock, hotkeys, [0.5 - i * 0.03 for i in range(6)])  # travel 0.15, no fire
    assert hotkeys == []
    eng.dispatch("pointer", hand_landmarks(), 0.5, AppSettings())  # leave open_palm
    run_swipe(eng, clock, hotkeys, [0.32 - i * 0.03 for i in range(6)])  # travel 0.15 alone
    assert hotkeys == []  # the pre-pause travel must not count


def test_swipe_disabled_by_setting():
    eng, clock, hotkeys, _ = swipe_engine()
    settings = AppSettings()
    settings.swipes.enabled = False
    for i in range(12):
        clock.advance(1.0 / 30.0)
        eng.dispatch("open_palm", swipe_landmarks(0.5 - i * 0.03), 0.5, settings)
    assert hotkeys == []


def test_swipe_preview_never_sends_hotkey(monkeypatch):
    import app.services.input_control as ic

    class Boom:
        def __getattr__(self, name):
            raise AssertionError("pyautogui must not be used in preview")

    monkeypatch.setattr(ic, "pyautogui", Boom())
    events = []
    ctl = InputController(dry_run=True)
    clock = FakeClock()
    eng = ControlEngine(ctl, VolumeController(dry_run=True), lambda e, d: events.append(e), clock=clock)
    run_swipe(eng, clock, [], [0.5 - i * 0.03 for i in range(12)])
    assert "SWIPE RIGHT" in events
    assert ctl.last_action == "hotkey alt+right"  # recorded, not sent


def test_reset_clears_baselines(engine):
    settings = AppSettings()
    engine.dispatch("pointer", hand_landmarks((0.5, 0.5)), 0.5, settings)
    engine.reset()
    assert engine._cursor_prev is None and engine._smoothed is None


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
