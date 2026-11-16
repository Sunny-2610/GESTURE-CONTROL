"""Static registry of the six gestures. Priority 1 is highest (Design.md 8.3)."""
from __future__ import annotations

from typing import Dict, List

from app.schemas.models import GestureInfo

# name -> (priority, title, pose description, action description, motion hint)
_GESTURES: Dict[str, tuple] = {
    "closed_fist": (
        1,
        "Closed fist",
        "All four fingers curled into the palm, thumb tucked.",
        "Pause: every action stops while the fist is held.",
        "Hold the fist to pause everything",
    ),
    "pinch_click": (
        2,
        "Pinch click",
        "Thumb tip touching the index tip.",
        "One mouse click each time the pinch closes.",
        "Hold a pinch for one click",
    ),
    "three_finger": (
        3,
        "Three-finger volume",
        "Index, middle and ring raised; pinky and thumb curled in.",
        "Media-key volume: hand up = louder, hand down = quieter.",
        "Move hand up or down",
    ),
    "two_finger_scroll": (
        4,
        "Two-finger scroll",
        "Index and middle raised in a V; ring and pinky curled.",
        "Joystick scroll: move up or down; farther from the anchor scrolls faster.",
        "Move hand up or down to scroll",
    ),
    "pointer": (
        5,
        "Pointer",
        "Only the index finger extended.",
        "Moves the cursor; hold still to dwell-click (when enabled).",
        "Hold still to dwell-click",
    ),
    "open_palm": (
        6,
        "Open palm",
        "All five fingers spread.",
        "Swipe left or right for browser back / forward.",
        "Swipe left or right",
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
            motion=_GESTURES[name][4],
            enabled=bool(enabled.get(name, True)),
        )
        for name in ORDER
    ]
