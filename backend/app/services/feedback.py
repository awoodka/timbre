"""Per-emotion feedback math.

Two pure functions used by the ratings API, the recommender, and the tests:
- `compute_resonance` derives an overall [0,1] score from one work's like/dislike map.
- `build_taste_profile` aggregates a user's marks across all their works into a
  31-dim weight vector (aligned to DIMENSION_KEYS) — their emotional taste profile.
"""

import numpy as np

from app.dimensions import DIMENSION_KEYS

# Confidence shrink: pulls a per-emotion weight toward 0 when there are few marks,
# so a single stray like/dislike can't dominate the whole profile.
PROFILE_SMOOTHING = 1.0


def compute_resonance(feedback: dict) -> float:
    """Overall [0,1] score from a graded feedback map (each mark in -2…+2):
    all-loved → 1.0, all-not-for-me → 0.0, balanced / empty → 0.5."""
    marks = [v for v in (feedback or {}).values() if v]
    if not marks:
        return 0.5
    return 0.5 + 0.5 * (sum(marks) / (2 * len(marks)))


def build_taste_profile(feedback_maps: list[dict]) -> np.ndarray:
    """Aggregate a user's per-emotion marks across all logged works into a 31-dim
    weight vector (DIMENSION_KEYS order). w_e = Σ marks_e / (count_e + K). Emotions
    the user never marked (incl. all structural dims) stay 0."""
    sums = {k: 0.0 for k in DIMENSION_KEYS}
    counts = {k: 0 for k in DIMENSION_KEYS}
    for fb in feedback_maps:
        for key, mark in (fb or {}).items():
            if key in sums:
                sums[key] += mark
                counts[key] += 1
    return np.array(
        [sums[k] / (counts[k] + PROFILE_SMOOTHING) if counts[k] else 0.0 for k in DIMENSION_KEYS],
        dtype=np.float64,
    )
