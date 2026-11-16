"""Heuristic gesture classification from MediaPipe hand landmarks.

Priority order (1 = highest, Design.md 8.3):
closed fist, pinch click, three-finger volume, two-finger scroll, pointer,
open palm.

The thumb is ignored for classification (thumb poses are unreliable); it is
only used inside the pinch distance (thumb tip <-> index tip).
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

# MediaPipe hand landmark indices
WRIST = 0
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_TIP = 12
RING_PIP = 14
RING_TIP = 16
PINKY_PIP = 18
PINKY_TIP = 20

TIP_PIP_PAIRS = [
    (THUMB_TIP, 2),          # thumb: tip vs IP joint
    (INDEX_TIP, INDEX_PIP),
    (MIDDLE_TIP, MIDDLE_PIP),
    (RING_TIP, RING_PIP),
    (PINKY_TIP, PINKY_PIP),
]

# extension pattern per pose, as (index, middle, ring, pinky); thumb ignored
POSE_TABLE = {
    "closed_fist": (False, False, False, False),
    "three_finger": (True, True, True, False),
    "two_finger_scroll": (True, True, False, False),
    "pointer": (True, False, False, False),
    "open_palm": (True, True, True, True),
}


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def fingers_extended(landmarks: Sequence[Sequence[float]]) -> List[bool]:
    """Five booleans (thumb..pinky): a finger counts extended when its tip is
    farther from the wrist than the reference joint.

    The thumb entry uses a clear margin (its tip is folded during a pinch);
    classification itself ignores it and only uses the thumb tip position for
    the pinch distance.
    """
    wrist = landmarks[WRIST]
    out: List[bool] = []
    for tip, ref in TIP_PIP_PAIRS:
        tip_dist = distance(landmarks[tip], wrist)
        ref_dist = distance(landmarks[ref], wrist)
        if tip == THUMB_TIP:
            # the thumb is folded during a pinch, so require a clear margin
            out.append(tip_dist > ref_dist * 1.15)
        else:
            out.append(tip_dist > ref_dist)
    return out


def pinch_distance(landmarks: Sequence[Sequence[float]]) -> float:
    return distance(landmarks[THUMB_TIP], landmarks[INDEX_TIP])


def hand_scale(landmarks: Sequence[Sequence[float]]) -> float:
    """Size of the palm in normalized image units (wrist -> middle MCP).

    Used to make every distance threshold invariant to how far the user sits
    from the camera.
    """
    scale = distance(landmarks[WRIST], landmarks[MIDDLE_MCP])
    if scale <= 1e-6:
        scale = distance(landmarks[WRIST], landmarks[INDEX_MCP])
    if scale <= 1e-6:
        scale = 1.0
    return scale


def pinch_ratio(landmarks: Sequence[Sequence[float]]) -> float:
    """Thumb-tip/index-tip distance expressed in palm sizes (scale invariant)."""
    return pinch_distance(landmarks) / hand_scale(landmarks)


PINCH_JOIN_RATIO = 0.30


def classify(
    landmarks: Sequence[Sequence[float]],
    extended: Optional[List[bool]] = None,
) -> Tuple[str, float]:
    """Return (gesture, confidence), evaluated in exactly the priority order.

    1 closed_fist       all four fingers curled (thumb ignored)  -> pause
    2 pinch_click       pinch ratio < PINCH_JOIN_RATIO and the other
                        three fingers not all extended (index state free)
    3 three_finger      index+middle+ring extended, pinky curled -> volume
    4 two_finger_scroll index+middle extended, ring+pinky curled -> scroll
    5 pointer           only the index extended                  -> cursor
    6 open_palm         all four extended                        -> swipe
    """
    if extended is None:
        extended = fingers_extended(landmarks)
    _thumb, index, middle, ring, pinky = extended
    fingers = (index, middle, ring, pinky)
    pinch = pinch_ratio(landmarks)

    if not any(fingers):
        return ("closed_fist", 0.95)
    if pinch < PINCH_JOIN_RATIO and not all((middle, ring, pinky)):
        return ("pinch_click", 0.9)
    if index and middle and ring and not pinky:
        return ("three_finger", 0.9)
    if index and middle and not ring and not pinky:
        return ("two_finger_scroll", 0.9)
    if index and not middle and not ring and not pinky:
        return ("pointer", 0.9)
    if all(fingers):
        return ("open_palm", 0.9)
    # fall back: closest pose by number of mismatches (thumb ignored)
    best_name, best_err = "pointer", 4
    for name in ("closed_fist", "three_finger", "two_finger_scroll", "pointer", "open_palm"):
        err = sum(1 for a, b in zip(fingers, POSE_TABLE[name]) if a != b)
        if err < best_err:
            best_name, best_err = name, err
    return (best_name, 0.5)


def pinch_active(landmarks: Sequence[Sequence[float]], threshold: float) -> bool:
    """True when the pinch is closed tighter than the given palm-size ratio."""
    return pinch_ratio(landmarks) < threshold
