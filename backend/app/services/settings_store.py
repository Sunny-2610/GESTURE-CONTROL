"""Settings persistence with validation. JSON file next to the backend package."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError

from app.schemas.models import AppSettings

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "settings.json"


class SettingsStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_PATH
        self._lock = threading.RLock()
        self._settings = AppSettings()
        self._saved = AppSettings()
        self.load()

    # -- state ------------------------------------------------------------

    def current(self) -> AppSettings:
        with self._lock:
            return self._settings.model_copy(deep=True)

    def saved(self) -> AppSettings:
        with self._lock:
            return self._saved.model_copy(deep=True)

    def unsaved_count(self) -> int:
        with self._lock:
            return _count_diff(self._saved, self._settings)

    # -- mutation ----------------------------------------------------------

    def update(self, patch: Dict) -> AppSettings:
        """Apply a partial update (nested dicts allowed). Raises ValueError."""
        with self._lock:
            merged = json.loads(self._settings.model_dump_json())
            _deep_merge(merged, patch)
            try:
                candidate = AppSettings.model_validate(merged)
            except ValidationError as exc:
                raise ValueError(_first_error_message(exc)) from exc
            self._settings = candidate
            return candidate

    def save(self) -> AppSettings:
        with self._lock:
            self._saved = self._settings.model_copy(deep=True)
            self._write(self._saved)
            return self._saved.model_copy(deep=True)

    def reset(self) -> AppSettings:
        with self._lock:
            self._settings = AppSettings()
            return self.current()

    # -- persistence ---------------------------------------------------------

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            raw = _migrate(raw)
            loaded = AppSettings.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValidationError):
            return
        with self._lock:
            self._saved = loaded
            self._settings = loaded.model_copy(deep=True)

    def _write(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(self.path)


def _migrate(raw: Dict) -> Dict:
    """Upgrade legacy absolute pinch thresholds to palm-size ratios."""
    click = raw.get("click")
    if isinstance(click, dict):
        threshold = click.get("pinch_threshold")
        if isinstance(threshold, (int, float)) and threshold < 0.15:
            click["pinch_threshold"] = 0.3
    return raw


def _deep_merge(base: Dict, patch: Dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _first_error_message(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid settings."
    err = errors[0]
    loc = ".".join(str(part) for part in err.get("loc", ()) if part != "input")
    return f"{loc or 'settings'}: {err.get('msg', 'invalid value')}"


def diff_fields(saved: AppSettings, current: AppSettings) -> List[Tuple[str, object, object]]:
    """Return (dotted-path, old, new) triples for every changed leaf."""
    out: List[Tuple[str, object, object]] = []
    _diff((), saved.model_dump(), current.model_dump(), out)
    return out


def _diff(prefix: tuple, old: Dict, new: Dict, out: List) -> None:
    for key, value in new.items():
        path = prefix + (key,)
        if isinstance(value, dict):
            _diff(path, old.get(key, {}), value, out)
        elif old.get(key) != value:
            out.append((".".join(path), old.get(key), value))


def _count_diff(saved: AppSettings, current: AppSettings) -> int:
    return len(diff_fields(saved, current))
