"""TV-show arc dimensions — ending_valence vs sourced tragic/uplifting endings.
Mirrors test_film_arc. Series endings are fuzzier, so the ground-truth sets are
restricted to clearly-agreed cases (tests/_helpers.py)."""

import numpy as np
import pytest

from tests._helpers import SHOW_ARC_TRAGIC, SHOW_ARC_UPLIFTING, score_of, present


@pytest.mark.parametrize("title", SHOW_ARC_TRAGIC)
def test_show_tragic_low_ending_valence(show_corpus, title):
    if title not in show_corpus:
        pytest.skip(f"{title} not in show corpus")
    ev = score_of(show_corpus, title, "ending_valence")
    assert ev <= 0.40, f"{title} has a bleak ending per consensus but ending_valence={ev:.2f}."


@pytest.mark.parametrize("title", SHOW_ARC_UPLIFTING)
def test_show_uplifting_high_ending_valence(show_corpus, title):
    if title not in show_corpus:
        pytest.skip(f"{title} not in show corpus")
    ev = score_of(show_corpus, title, "ending_valence")
    assert ev >= 0.60, f"{title} has an uplifting ending per consensus but ending_valence={ev:.2f}."


def test_show_ending_valence_separates_arcs(show_corpus):
    trag = [score_of(show_corpus, t, "ending_valence") for t in present(show_corpus, SHOW_ARC_TRAGIC)]
    upl = [score_of(show_corpus, t, "ending_valence") for t in present(show_corpus, SHOW_ARC_UPLIFTING)]
    assert np.mean(trag) + 0.30 < np.mean(upl), (
        f"ending_valence not separating show arcs: tragic mean={np.mean(trag):.2f} vs uplifting mean={np.mean(upl):.2f}"
    )


def test_show_arc_dims_carry_signal(show_corpus):
    for dim in ("emotional_trajectory", "ending_valence"):
        vals = np.array([b["scores"][dim] for b in show_corpus.values()])
        assert vals.std() > 0.15, f"{dim} has too little spread across shows (std={vals.std():.2f})"
