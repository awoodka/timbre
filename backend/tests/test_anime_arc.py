"""Anime arc dimensions — ending_valence vs sourced tragic/uplifting endings."""

import numpy as np
import pytest

from tests._helpers import ANIME_ARC_TRAGIC, ANIME_ARC_UPLIFTING, score_of, present


@pytest.mark.parametrize("title", ANIME_ARC_TRAGIC)
def test_anime_tragic_low_ending_valence(anime_corpus, title):
    if title not in anime_corpus:
        pytest.skip(f"{title} not in anime corpus")
    ev = score_of(anime_corpus, title, "ending_valence")
    assert ev <= 0.40, f"{title} has a tragic ending per consensus but ending_valence={ev:.2f}."


@pytest.mark.parametrize("title", ANIME_ARC_UPLIFTING)
def test_anime_uplifting_high_ending_valence(anime_corpus, title):
    if title not in anime_corpus:
        pytest.skip(f"{title} not in anime corpus")
    ev = score_of(anime_corpus, title, "ending_valence")
    assert ev >= 0.60, f"{title} has an uplifting ending per consensus but ending_valence={ev:.2f}."


def test_anime_ending_valence_separates_arcs(anime_corpus):
    trag = [score_of(anime_corpus, t, "ending_valence") for t in present(anime_corpus, ANIME_ARC_TRAGIC)]
    upl = [score_of(anime_corpus, t, "ending_valence") for t in present(anime_corpus, ANIME_ARC_UPLIFTING)]
    assert np.mean(trag) + 0.30 < np.mean(upl), (
        f"ending_valence not separating anime arcs: tragic={np.mean(trag):.2f} vs uplifting={np.mean(upl):.2f}"
    )


def test_anime_arc_dims_carry_signal(anime_corpus):
    for dim in ("emotional_trajectory", "ending_valence"):
        vals = np.array([b["scores"][dim] for b in anime_corpus.values()])
        assert vals.std() > 0.15, f"{dim} too little spread across anime (std={vals.std():.2f})"
