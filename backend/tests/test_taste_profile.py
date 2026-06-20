"""Unit tests for the per-emotion feedback math (resonance + taste profile)."""

import numpy as np

from app.dimensions import DIMENSION_KEYS
from app.services.feedback import (
    PROFILE_SMOOTHING,
    build_taste_profile,
    compute_resonance,
)


def _w(maps, key):
    return build_taste_profile(maps)[DIMENSION_KEYS.index(key)]


def test_resonance_extremes_and_balance():
    assert compute_resonance({"a": 2, "b": 2}) == 1.0     # all loved
    assert compute_resonance({"a": -2, "b": -2}) == 0.0   # all not-for-me
    assert compute_resonance({}) == 0.5                   # nothing marked
    assert compute_resonance({"a": 2, "b": -2}) == 0.5    # balanced
    assert compute_resonance({"a": 1}) == 0.75            # liked, not loved


def test_taste_profile_sign_and_confidence_shrink():
    # liked melancholy twice → +2/(2+K); disliked dread once → -1/(1+K)
    assert _w([{"melancholy": 1}, {"melancholy": 1}], "melancholy") == 2 / (2 + PROFILE_SMOOTHING)
    assert _w([{"dread": -1}], "dread") == -1 / (1 + PROFILE_SMOOTHING)
    # one like is shrunk toward 0 (less confident than two)
    assert _w([{"melancholy": 1}], "melancholy") < _w([{"melancholy": 1}, {"melancholy": 1}], "melancholy")
    # an emotion the user never marked stays exactly 0
    assert _w([{"melancholy": 1}], "joy") == 0.0


def test_mixed_marks_net_out():
    # liked once, disliked once → net 0
    assert _w([{"warmth": 1}, {"warmth": -1}], "warmth") == 0.0


def test_profile_is_31_dims_aligned_to_keys():
    w = build_taste_profile([{"melancholy": 1}])
    assert w.shape == (len(DIMENSION_KEYS),)
    assert isinstance(w, np.ndarray)
