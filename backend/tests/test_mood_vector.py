"""Unit tests for the experience-search mood-vector math (build + blend)."""

import numpy as np

from app.dimensions import DIMENSION_KEYS, NUM_DIMENSIONS
from app.services.feedback import build_taste_profile
from app.services.mood import blend_vectors, build_mood_vector


def _i(key):
    return DIMENSION_KEYS.index(key)


def test_seek_and_avoid_signs():
    v = build_mood_vector({"warmth": 1, "dread": -1})
    assert v[_i("warmth")] == 1.0
    assert v[_i("dread")] == -1.0
    assert v[_i("joy")] == 0.0          # unmarked stays 0
    assert v.shape == (NUM_DIMENSIONS,)


def test_structural_and_unknown_keys_ignored():
    # a structural axis and a junk key both leave the vector untouched
    assert not build_mood_vector({"ending_valence": 1, "not_a_key": -1}).any()


def test_blend_pure_mood_when_taste_zero():
    mood = build_mood_vector({"warmth": 1})
    out = blend_vectors(mood, np.zeros(NUM_DIMENSIONS), alpha=0.6)
    assert np.allclose(out, mood / np.linalg.norm(mood))


def test_blend_pure_taste_when_mood_zero():
    taste = build_taste_profile([{"dread": 1}])
    out = blend_vectors(np.zeros(NUM_DIMENSIONS), taste, alpha=0.6)
    assert np.allclose(out, taste / np.linalg.norm(taste))


def test_blend_both_zero_is_zero():
    out = blend_vectors(np.zeros(NUM_DIMENSIONS), np.zeros(NUM_DIMENSIONS), 0.5)
    assert float(np.linalg.norm(out)) == 0.0


def test_blend_is_unit_norm_when_nonzero():
    out = blend_vectors(build_mood_vector({"warmth": 1}), build_mood_vector({"dread": 1}), 0.5)
    assert np.isclose(float(np.linalg.norm(out)), 1.0)


def test_higher_alpha_leans_toward_mood():
    m = build_mood_vector({"warmth": 1})
    t = build_mood_vector({"dread": 1})
    m_hat = m / np.linalg.norm(m)
    hi = float(blend_vectors(m, t, 0.9) @ m_hat)
    lo = float(blend_vectors(m, t, 0.1) @ m_hat)
    assert hi > lo
