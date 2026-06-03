"""Film arc dimensions — ending_valence vs sourced tragic/uplifting endings.
Mirrors test_arc_discrimination on films. Ground truth: tests/_helpers.py."""

import numpy as np
import pytest

from tests._helpers import FILM_ARC_TRAGIC, FILM_ARC_UPLIFTING, score_of, present


@pytest.mark.parametrize("title", FILM_ARC_TRAGIC)
def test_film_tragic_low_ending_valence(film_corpus, title):
    if title not in film_corpus:
        pytest.skip(f"{title} not in film corpus")
    ev = score_of(film_corpus, title, "ending_valence")
    assert ev <= 0.35, (
        f"{title} has a bleak/tragic ending per consensus but ending_valence={ev:.2f}."
    )


@pytest.mark.parametrize("title", FILM_ARC_UPLIFTING)
def test_film_uplifting_high_ending_valence(film_corpus, title):
    if title not in film_corpus:
        pytest.skip(f"{title} not in film corpus")
    ev = score_of(film_corpus, title, "ending_valence")
    assert ev >= 0.60, (
        f"{title} has an uplifting ending per consensus but ending_valence={ev:.2f}."
    )


def test_film_ending_valence_separates_arcs(film_corpus):
    trag = [score_of(film_corpus, t, "ending_valence") for t in present(film_corpus, FILM_ARC_TRAGIC)]
    upl = [score_of(film_corpus, t, "ending_valence") for t in present(film_corpus, FILM_ARC_UPLIFTING)]
    assert np.mean(trag) + 0.30 < np.mean(upl), (
        f"ending_valence not separating film arcs: tragic mean={np.mean(trag):.2f} vs uplifting mean={np.mean(upl):.2f}"
    )


def test_film_arc_dims_carry_signal(film_corpus):
    for dim in ("emotional_trajectory", "ending_valence"):
        vals = np.array([b["scores"][dim] for b in film_corpus.values()])
        assert vals.std() > 0.15, f"{dim} has too little spread across films (std={vals.std():.2f})"
