"""Mood-vector math for experience search.

Two pure functions, mirroring services/feedback.py, used by the recommender's
experience-search mode (compose the emotional experience you want):

- `build_mood_vector` turns a seek/avoid feeling map into a 31-dim *direction*
  vector — the same raw signed-sum space as a taste profile, so the two blend
  coherently and rank correctly against the standardized (mean-centered) corpus
  vectors (where a positive weight rewards above-average works on that axis and a
  negative weight pushes the opposite way).
- `blend_vectors` mixes a mood direction with a taste direction by a dial α,
  unit-normalizing each first so α is a true blend of *directions* (otherwise a
  many-key mood would swamp a one-key taste regardless of α).
"""

import numpy as np

from app.dimensions import DIMENSION_KEYS, FELT_KEYS, NUM_DIMENSIONS

_FELT_SET = set(FELT_KEYS)
_INDEX = {k: i for i, k in enumerate(DIMENSION_KEYS)}


def build_mood_vector(mood: dict) -> np.ndarray:
    """A 31-dim direction vector (DIMENSION_KEYS order) from a seek/avoid map
    `{felt_key: +1 (seek) | -1 (avoid)}`. Non-felt / unknown keys are ignored
    (the schema validates, but be defensive). Returned un-normalized; the caller
    normalizes after blending."""
    v = np.zeros(NUM_DIMENSIONS, dtype=np.float64)
    for key, mark in (mood or {}).items():
        i = _INDEX.get(key)
        if i is not None and key in _FELT_SET and mark:
            v[i] = 1.0 if mark > 0 else -1.0
    return v


def _unit(x: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(x))
    return x / n if n > 0 else x


def blend_vectors(mood_vec: np.ndarray, taste_vec: np.ndarray, alpha: float) -> np.ndarray:
    """`normalize(α·normalize(mood) + (1−α)·normalize(taste))`.

    Each input is unit-normalized first so α is a true mix of two directions.
    Degenerate cases collapse cleanly: taste==0 → pure mood (the ungated path);
    mood==0 → pure taste; both 0 → the zero vector (the caller returns empty)."""
    blended = alpha * _unit(mood_vec) + (1.0 - alpha) * _unit(taste_vec)
    return _unit(blended)
