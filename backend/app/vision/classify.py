"""Heuristic gesture classification from MediaPipe hand landmarks.

Priority order (1 = highest, Design.md 8.3):
closed fist, volume mode, two-finger scroll, pinch click, pointer, open palm.
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

POSE_TABLE = {
    "closed_fist": (False, False, False, False),
    "volume_mode": (True, False, False, False),
    "two_finger_scroll": (False, True, True, False),
    "pointer": (False, True, False, False),
    "open_palm": (True, True, True, True),
}


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def fingers_extended(landmarks: Sequence[Sequence[float]]) -> List[bool]:
    """Five booleans (thumb..pinky): a finger counts extended when its tip is
    farther from the wrist than the reference joint."""
    wrist = landmarks[WRIST]
    out: List[bool] = []
    for tip, ref in TIP_PIP_PAIRS:
        out.append(distance(landmarks[tip], wrist) > distance(landmarks[ref], wrist))
    return out


def pinch_distance(landmarks: Sequence[Sequence[float]]) -> float:
    return distance(landmarks[THUMB_TIP], landmarks[INDEX_TIP])


PINCH_JOIN_DISTANCE = 0.12


def classify(
    landmarks: Sequence[Sequence[float]],
    extended: Optional[List[bool]] = None,
) -> Tuple[str, float]:
    """Return (gesture, confidence). Confidence is a simple landmark-spread score."""
    if extended is None:
        extended = fingers_extended(landmarks)
    thumb, index, middle, ring, pinky = extended
    fingers = [index, middle, ring, pinky]
    four_curled = not any(fingers)
    pinch = pinch_distance(landmarks)

    if four_curled and not thumb:
        return ("closed_fist", 0.95)
    if four_curled and thumb:
        return ("volume_mode", 0.85)
    if index and middle and not ring and not pinky:
        return ("two_finger_scroll", 0.9)
    if not (middle or ring or pinky):
        # only the index is extended (thumb state free)
        if pinch < PINCH_JOIN_DISTANCE:
            return ("pinch_click", 0.9)
        return ("pointer", 0.9)
    if all(fingers):
        return ("open_palm", 0.9)
    # fall back: closest pose by number of mismatches
    best_name, best_err = "pointer", 5
    for name in ("closed_fist", "volume_mode", "two_finger_scroll", "pointer", "open_palm"):
        target = POSE_TABLE[name]
        states = (thumb, index, middle, pinky)
        err = sum(1 for a, b in zip(states, target) if a != b)
        if err < best_err:
            best_name, best_err = name, err
    return (best_name, 0.5)


def pinch_active(landmarks: Sequence[Sequence[float]], threshold: float) -> bool:
    return pinch_distance(landmarks) < threshold
