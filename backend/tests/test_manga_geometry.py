"""Manga embedding-space health — same invariants as test_geometry, manga only."""

import numpy as np
import pytest

from app.dimensions import NUM_DIMENSIONS, DIMENSION_KEYS
from tests._helpers import cosine


def test_every_manga_has_full_finite_vector(manga_corpus):
    for title, b in manga_corpus.items():
        v = b["vec"]
        assert len(v) == NUM_DIMENSIONS, f"{title}: {len(v)} dims"
        assert np.all(np.isfinite(v)), f"{title}: non-finite"
        assert float(np.linalg.norm(v)) > 0, f"{title}: zero vector"


def test_manga_vectors_unit_normalized(manga_corpus):
    for title, b in manga_corpus.items():
        n = float(np.linalg.norm(b["vec"]))
        assert abs(n - 1.0) < 1e-6, f"{title}: norm {n:.4f}"


def test_manga_space_discriminates(manga_corpus):
    titles = list(manga_corpus)
    sims = [cosine(manga_corpus[a]["vec"], manga_corpus[b]["vec"])
            for i, a in enumerate(titles) for b in titles[i + 1:]]
    m = float(np.mean(sims))
    assert m < 0.40, f"Mean pairwise manga cosine {m:.3f} too high — narrow cone."


def test_no_near_duplicate_manga(manga_corpus):
    titles = list(manga_corpus)
    off = [(a, b) for i, a in enumerate(titles) for b in titles[i + 1:]
           if cosine(manga_corpus[a]["vec"], manga_corpus[b]["vec"]) > 0.97]
    assert not off, f"Near-duplicate manga: {off}"


def test_no_dead_dimension_in_manga(manga_corpus):
    mat = np.array([[b["scores"][k] for k in DIMENSION_KEYS] for b in manga_corpus.values()])
    dead = [DIMENSION_KEYS[i] for i, sd in enumerate(mat.std(axis=0)) if sd < 0.05]
    assert not dead, f"Dead manga dimensions: {dead}"


def test_manga_health_report(manga_corpus, capsys):
    titles = list(manga_corpus)
    sims = [cosine(manga_corpus[a]["vec"], manga_corpus[b]["vec"])
            for i, a in enumerate(titles) for b in titles[i + 1:]]
    with capsys.disabled():
        print(f"\n--- MANGA HEALTH --- n={len(titles)} mean_cos={np.mean(sims):.3f} "
              f"min={np.min(sims):.3f} max={np.max(sims):.3f}")
    assert np.mean(sims) < 0.40
