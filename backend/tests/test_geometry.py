"""Embedding-space health: shape, finiteness, standardization, discrimination.

These are invariants of a *useful* vector space, independent of any one book.
They catch regressions like the pre-standardization "narrow cone" problem and
dead/constant dimensions (e.g. the old emotional_complexity ~0.80/0.12).
"""

import numpy as np
import pytest

from app.dimensions import NUM_DIMENSIONS, DIMENSION_KEYS
from tests._helpers import cosine


def test_every_book_has_a_full_finite_vector(corpus):
    for title, b in corpus.items():
        v = b["vec"]
        assert len(v) == NUM_DIMENSIONS, f"{title}: {len(v)} dims, expected {NUM_DIMENSIONS}"
        assert np.all(np.isfinite(v)), f"{title}: non-finite values in vector"
        assert float(np.linalg.norm(v)) > 0, f"{title}: zero vector"


def test_vectors_are_unit_normalized(corpus):
    for title, b in corpus.items():
        norm = float(np.linalg.norm(b["vec"]))
        assert abs(norm - 1.0) < 1e-6, f"{title}: vector norm {norm:.4f}, expected 1.0"


def test_breakdown_keys_match_dimensions(corpus):
    expected = set(DIMENSION_KEYS)
    for title, b in corpus.items():
        assert set(b["scores"]) == expected, f"{title}: breakdown keys != dimensions"


def test_space_is_discriminating_not_a_narrow_cone(corpus):
    """Standardization should spread books out: mean pairwise cosine ~0, not ~0.7.

    (Raw [0,1] vectors sat at ~0.69 — everything looked similar. Mean-centering
    must keep this low or discrimination is lost.)
    """
    titles = list(corpus)
    sims = [
        cosine(corpus[a]["vec"], corpus[b]["vec"])
        for i, a in enumerate(titles)
        for b in titles[i + 1:]
    ]
    mean_sim = float(np.mean(sims))
    assert mean_sim < 0.30, (
        f"Mean pairwise cosine {mean_sim:.3f} is too high — books are crammed into "
        "a narrow cone (weak discrimination). Standardization may be off."
    )


def test_no_near_duplicate_vectors(corpus):
    """No two distinct books should be near-identical (cosine > 0.97)."""
    titles = list(corpus)
    offenders = [
        (a, b, cosine(corpus[a]["vec"], corpus[b]["vec"]))
        for i, a in enumerate(titles)
        for b in titles[i + 1:]
        if cosine(corpus[a]["vec"], corpus[b]["vec"]) > 0.97
    ]
    assert not offenders, f"Near-duplicate vectors: {offenders}"


def test_no_dead_or_constant_dimension(corpus):
    """Every dimension must carry signal (spread) across the corpus.

    Guards against a dimension collapsing to a near-constant (the old
    emotional_complexity inflation), which adds no discriminating information.
    """
    mat = np.array([[b["scores"][k] for k in DIMENSION_KEYS] for b in corpus.values()])
    stdevs = mat.std(axis=0)
    dead = [DIMENSION_KEYS[i] for i, sd in enumerate(stdevs) if sd < 0.05]
    assert not dead, f"Dimensions with near-zero variance (no signal): {dead}"


def test_health_report(corpus, capsys):
    """Always-on diagnostic snapshot (run with -s to view). Asserts only the
    headline invariant; the printout surfaces where the space may be weak."""
    titles = list(corpus)
    sims = [
        cosine(corpus[a]["vec"], corpus[b]["vec"])
        for i, a in enumerate(titles)
        for b in titles[i + 1:]
    ]
    mat = np.array([[b["scores"][k] for k in DIMENSION_KEYS] for b in corpus.values()])
    with capsys.disabled():
        print("\n--- EMBEDDING HEALTH REPORT ---")
        print(f"books={len(titles)}  mean_cos={np.mean(sims):.3f}  "
              f"min={np.min(sims):.3f}  max={np.max(sims):.3f}")
        order = np.argsort(-mat.mean(axis=0))
        print("highest-mean dims (potential shared baseline):")
        for i in order[:5]:
            print(f"   {DIMENSION_KEYS[i]:22} mean={mat[:,i].mean():.2f} std={mat[:,i].std():.2f}")
        print("lowest-variance dims (weakest signal):")
        for i in np.argsort(mat.std(axis=0))[:5]:
            print(f"   {DIMENSION_KEYS[i]:22} std={mat[:,i].std():.2f}")
    assert np.mean(sims) < 0.30
