import pytest

from app.vision.classify import classify, fingers_extended, pinch_distance

# Wrist at bottom center; finger landmarks spread upward when extended.
WRIST = [0.5, 0.9, 0.0]


def hand(tips_y, refs_y, thumb_tip=[0.4, 0.6], thumb_ref=[0.38, 0.7], pinch_gap=None):
    """Build a plausible 21-point hand. tips_y/refs_y: y of tip vs ref joint per
    finger (index, middle, ring, pinky). Larger y = lower = closer to wrist."""
    lm = [[0.0, 0.0, 0.0] for _ in range(21)]
    lm[0] = list(WRIST)
    # thumb
    lm[2] = list(thumb_ref)
    lm[4] = list(thumb_tip)
    # index MCP / PIP / TIP etc.
    xs = [0.55, 0.60, 0.65, 0.70]
    mcp_y = [0.65, 0.63, 0.65, 0.68]
    for i, (tip_y, ref_y) in enumerate(zip(tips_y, refs_y)):
        base = i * 4 + 5
        lm[base] = [xs[i], mcp_y[i], 0.0]
        lm[base + 1] = [xs[i], ref_y, 0.0]   # PIP
        lm[base + 2] = [xs[i], (ref_y + tip_y) / 2, 0.0]  # DIP
        lm[base + 3] = [xs[i], tip_y, 0.0]
    if pinch_gap is not None:
        lm[4] = [0.55, 0.65, 0.0]  # thumb tip near index tip
        lm[8] = [0.55, 0.65 + pinch_gap, 0.0]
    return lm


def test_fist():
    # curled: tip pulled back toward the wrist (larger y) beyond the ref joint
    lm = hand(tips_y=[0.74, 0.72, 0.74, 0.76], refs_y=[0.70, 0.68, 0.70, 0.73],
              thumb_tip=[0.42, 0.78], thumb_ref=[0.40, 0.70])
    ext = fingers_extended(lm)
    assert not ext[1] and not ext[2] and not ext[3] and not ext[4]
    assert not ext[0]
    gesture, _ = classify(lm, ext)
    assert gesture == "closed_fist"


def test_open_palm():
    lm = hand(tips_y=[0.30, 0.25, 0.28, 0.32], refs_y=[0.55, 0.53, 0.55, 0.58])
    ext = fingers_extended(lm)
    assert all(ext[1:])
    gesture, _ = classify(lm, ext)
    assert gesture == "open_palm"


def test_pointer():
    lm = hand(tips_y=[0.30, 0.72, 0.70, 0.74], refs_y=[0.55, 0.66, 0.68, 0.72])
    ext = fingers_extended(lm)
    assert ext[1] and not ext[2]
    gesture, _ = classify(lm, ext)
    assert gesture == "pointer"


def test_two_finger_scroll():
    lm = hand(tips_y=[0.30, 0.28, 0.72, 0.74], refs_y=[0.55, 0.53, 0.68, 0.72])
    ext = fingers_extended(lm)
    assert ext[1] and ext[2] and not ext[3] and not ext[4]
    gesture, _ = classify(lm, ext)
    assert gesture == "two_finger_scroll"


def test_volume_mode():
    lm = hand(tips_y=[0.74, 0.72, 0.74, 0.76], refs_y=[0.68, 0.66, 0.68, 0.72],
              thumb_tip=[0.35, 0.55], thumb_ref=[0.38, 0.70])
    ext = fingers_extended(lm)
    assert ext[0] and not ext[1] and not ext[2]
    gesture, _ = classify(lm, ext)
    assert gesture == "volume_mode"


def test_fist_overrides_pointer_when_all_curled():
    lm = hand(tips_y=[0.74, 0.72, 0.74, 0.76], refs_y=[0.68, 0.66, 0.68, 0.72],
              thumb_tip=[0.42, 0.78], thumb_ref=[0.40, 0.70])
    ext = fingers_extended(lm)
    assert not ext[1]
    gesture, _ = classify(lm, ext)
    assert gesture == "closed_fist"


def test_pinch_distance():
    lm = hand(tips_y=[0.30, 0.25, 0.28, 0.32], refs_y=[0.55, 0.53, 0.55, 0.58],
              pinch_gap=0.03)
    assert pinch_distance(lm) < 0.05
