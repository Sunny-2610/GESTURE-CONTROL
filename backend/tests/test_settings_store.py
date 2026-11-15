import pytest

from app.services.settings_store import SettingsStore, diff_fields


@pytest.fixture()
def store(tmp_path) -> SettingsStore:
    return SettingsStore(path=tmp_path / "settings.json")


def test_defaults(store):
    s = store.current()
    assert s.cursor.control_hand == "right"
    assert s.click.pinch_threshold == 0.06
    assert s.safety.auto_disable_on_disconnect is True
    assert store.unsaved_count() == 0


def test_partial_update_and_save(store, tmp_path):
    store.update({"cursor": {"sensitivity": 2.0}})
    assert store.current().cursor.sensitivity == 2.0
    assert store.unsaved_count() == 1
    store.save()
    assert store.unsaved_count() == 0

    reloaded = SettingsStore(path=tmp_path / "settings.json")
    assert reloaded.current().cursor.sensitivity == 2.0
    assert reloaded.current().cursor.smoothing == 0.5


def test_validation_rejects_out_of_range(store):
    with pytest.raises(ValueError):
        store.update({"cursor": {"sensitivity": 99.0}})
    # current settings unchanged
    assert store.current().cursor.sensitivity == 1.5


def test_validation_message_names_field(store):
    with pytest.raises(ValueError) as err:
        store.update({"click": {"cooldown": 0.01}})
    assert "click.cooldown" in str(err.value)


def test_reset(store):
    store.update({"scroll": {"speed": 3.0}})
    store.reset()
    assert store.current().scroll.speed == 1.0


def test_diff_fields(store):
    store.update({"cursor": {"sensitivity": 2.5}, "click": {"double_click": True}})
    diffs = dict((name, (old, new)) for name, old, new in diff_fields(store.saved(), store.current()))
    assert diffs["cursor.sensitivity"] == (1.5, 2.5)
    assert diffs["click.double_click"] == (False, True)
    assert store.unsaved_count() == 2


def test_gesture_toggles_roundtrip(store):
    store.update({"gestures": {"closed_fist": False}})
    store.save()
    reloaded = SettingsStore(path=store.path)
    assert reloaded.current().gestures.closed_fist is False
