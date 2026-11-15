"""Static registry of the six gestures. Priority 1 is highest (Design.md 8.3)."""
from __future__ import annotations

from typing import Dict, List

from app.schemas.models import GestureInfo

# name -> (priority, title, pose description, action description)
_GESTURES: Dict[str, tuple] = {
    "closed_fist": (
        1,
        "Closed fist",
        "All fingers curled into the palm.",
        "Rest pose. All actions stop while held.",
    ),
    "volume_mode": (
        2,
        "Volume mode",
        "Thumb out, other fingers curled.",
        "Move up or down to set master volume.",
    ),
    "two_finger_scroll": (
        3,
        "Two-finger scroll",
        "Index and middle extended, ring and pinky curled.",
        "Move vertically to scroll the page.",
    ),
    "pinch_click": (
        4,
        "Pinch click",
        "Thumb tip touches index tip.",
        "Clicks the mouse once per pinch.",
    ),
    "pointer": (
        5,
        "Pointer",
        "Only the index finger extended.",
        "Moves the cursor inside the active region.",
    ),
    "open_palm": (
        6,
        "Open palm",
        "All five fingers extended.",
        "Neutral pose. Nothing is dispatched.",
    ),
}

ORDER: List[str] = sorted(_GESTURES, key=lambda name: _GESTURES[name][0])


def build_registry(enabled: Dict[str, bool]) -> List[GestureInfo]:
    return [
        GestureInfo(
            name=name,
            priority=_GESTURES[name][0],
            title=_GESTURES[name][1],
            pose=_GESTURES[name][2],
            action=_GESTURES[name][3],
            enabled=bool(enabled.get(name, True)),
        )
        for name in ORDER
    ]
