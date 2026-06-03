"""Film embedding-space health — same invariants as test_geometry, films only."""

import numpy as np
import pytest

from app.dimensions import NUM_DIMENSIONS, DIMENSION_KEYS
from tests._helpers import cosine


def test_every_film_has_full_finite_vector(film_corpus):
    for title, b in film_corpus.items():
        v = b["vec"]
        assert len(v) == NUM_DIMENSIONS, f"{title}: {len(v)} dims, expected {NUM_DIMENSIONS}"
        assert np.all(np.isfinite(v)), f"{title}: non-finite values"
        assert float(np.linalg.norm(v)) > 0, f"{title}: zero vector"


def test_film_vectors_unit_normalized(film_corpus):
    for title, b in film_corpus.items():
        n = float(np.linalg.norm(b["vec"]))
        assert abs(n - 1.0) < 1e-6, f"{title}: norm {n:.4f}"


def test_film_space_discriminates(film_corpus):
    titles = list(film_corpus)
    sims = [cosine(film_corpus[a]["vec"], film_corpus[b]["vec"])
            for i, a in enumerate(titles) for b in titles[i + 1:]]
    m = float(np.mean(sims))
    assert m < 0.40, f"Mean pairwise film cosine {m:.3f} too high — films crammed into a narrow cone."


def test_no_near_duplicate_films(film_corpus):
    titles = list(film_corpus)
    off = [(a, b, round(cosine(film_corpus[a]["vec"], film_corpus[b]["vec"]), 3))
           for i, a in enumerate(titles) for b in titles[i + 1:]
           if cosine(film_corpus[a]["vec"], film_corpus[b]["vec"]) > 0.97]
    assert not off, f"Near-duplicate film vectors: {off}"


def test_no_dead_dimension_in_films(film_corpus):
    mat = np.array([[b["scores"][k] for k in DIMENSION_KEYS] for b in film_corpus.values()])
    dead = [DIMENSION_KEYS[i] for i, sd in enumerate(mat.std(axis=0)) if sd < 0.05]
    assert not dead, f"Film dimensions with near-zero variance: {dead}"


def test_film_health_report(film_corpus, capsys):
    titles = list(film_corpus)
    sims = [cosine(film_corpus[a]["vec"], film_corpus[b]["vec"])
            for i, a in enumerate(titles) for b in titles[i + 1:]]
    mat = np.array([[b["scores"][k] for k in DIMENSION_KEYS] for b in film_corpus.values()])
    with capsys.disabled():
        print(f"\n--- FILM HEALTH REPORT --- films={len(titles)} "
              f"mean_cos={np.mean(sims):.3f} min={np.min(sims):.3f} max={np.max(sims):.3f}")
        for i in np.argsort(-mat.mean(axis=0))[:5]:
            print(f"   {DIMENSION_KEYS[i]:22} mean={mat[:, i].mean():.2f} std={mat[:, i].std():.2f}")
    assert np.mean(sims) < 0.40
