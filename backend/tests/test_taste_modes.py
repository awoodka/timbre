"""Unit tests for multi-modal taste clustering + MMR (pure, no DB).

Mirrors test_enjoyment_affinity.py: small hand-built arrays exercise the pure
functions in services/taste_modes.py.
"""

import numpy as np

from app.services.taste_modes import cluster_taste_modes, mmr_rerank


def _unit_rows(arr):
    arr = np.asarray(arr, dtype=np.float64)
    return arr / np.linalg.norm(arr, axis=1, keepdims=True)


def test_two_distinct_modes_split():
    # Two clearly separated groups → two modes, three works each.
    a = _unit_rows([[1, 0, 0, 0], [0.95, 0.05, 0, 0], [0.9, 0.1, 0.05, 0]])
    b = _unit_rows([[0, 0, 1, 0], [0, 0.05, 0.95, 0], [0, 0, 0.9, 0.1]])
    modes = cluster_taste_modes(np.vstack([a, b]), np.ones(6))
    assert len(modes) == 2
    assert sorted(len(m["indices"]) for m in modes) == [3, 3]


def test_one_coherent_taste_single_mode():
    # One tight isotropic blob → no clean split → a single mode.
    rng = np.random.default_rng(0)
    base = np.array([1.0, 0.2, 0.1, 0.0])
    X = _unit_rows([base + 0.01 * rng.standard_normal(4) for _ in range(6)])
    modes = cluster_taste_modes(X, np.ones(6))
    assert len(modes) == 1
    assert len(modes[0]["indices"]) == 6


def test_too_few_works_single_mode():
    X = _unit_rows([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # n=3 < 2*MIN_MODE_WORKS
    assert len(cluster_taste_modes(X, np.ones(3))) == 1


def test_weights_pull_centroid():
    X = _unit_rows([[1, 0], [0, 1]])
    heavy = cluster_taste_modes(X, np.array([5.0, 1.0]))[0]["centroid"]
    light = cluster_taste_modes(X, np.array([1.0, 5.0]))[0]["centroid"]
    assert heavy[0] > heavy[1]   # pulled toward [1, 0]
    assert light[1] > light[0]   # pulled toward [0, 1]


def test_centroid_is_unit_norm():
    X = _unit_rows([[1, 0, 0], [0.8, 0.6, 0], [0, 1, 0]])
    for m in cluster_taste_modes(X, np.ones(3)):
        assert np.isclose(np.linalg.norm(m["centroid"]), 1.0)


def test_mmr_lambda_one_is_relevance_order():
    q = np.array([1.0, 0.0])
    V = _unit_rows([[1, 0], [0.9, 0.1], [0.7, 0.3], [0, 1]])
    order = mmr_rerank(V, q, k=4, lam=1.0)
    assert order == list(np.argsort(-(V @ q)))


def test_mmr_diversity_demotes_near_duplicate():
    # Candidate 1 is a near-duplicate of the top pick (0); candidate 2 is distinct.
    # With diversity, the 2nd slot goes to the distinct one, not the near-duplicate.
    q = np.array([1.0, 0.0])
    V = _unit_rows([[1, 0], [0.995, 0.1], [0.6, 0.8]])
    assert mmr_rerank(V, q, k=2, lam=0.3) == [0, 2]


def test_mmr_empty():
    assert mmr_rerank(np.zeros((0, 3)), np.array([1.0, 0, 0]), k=5) == []
