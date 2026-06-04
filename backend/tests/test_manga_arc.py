"""Manga arc dimensions — ending_valence vs sourced tragic/uplifting endings.
(Manga endings are fuzzy/long-running, so the ground-truth sets are small.)"""

import numpy as np
import pytest

from tests._helpers import MANGA_ARC_TRAGIC, MANGA_ARC_UPLIFTING, score_of, present


@pytest.mark.parametrize("title", MANGA_ARC_TRAGIC)
def test_manga_tragic_low_ending_valence(manga_corpus, title):
    if title not in manga_corpus:
        pytest.skip(f"{title} not in manga corpus")
    ev = score_of(manga_corpus, title, "ending_valence")
    assert ev <= 0.40, f"{title} has a bleak ending per consensus but ending_valence={ev:.2f}."


@pytest.mark.parametrize("title", MANGA_ARC_UPLIFTING)
def test_manga_uplifting_high_ending_valence(manga_corpus, title):
    if title not in manga_corpus:
        pytest.skip(f"{title} not in manga corpus")
    ev = score_of(manga_corpus, title, "ending_valence")
    assert ev >= 0.60, f"{title} has an uplifting ending per consensus but ending_valence={ev:.2f}."


def test_manga_ending_valence_separates_arcs(manga_corpus):
    trag = [score_of(manga_corpus, t, "ending_valence") for t in present(manga_corpus, MANGA_ARC_TRAGIC)]
    upl = [score_of(manga_corpus, t, "ending_valence") for t in present(manga_corpus, MANGA_ARC_UPLIFTING)]
    assert np.mean(trag) + 0.25 < np.mean(upl), (
        f"ending_valence not separating manga arcs: tragic={np.mean(trag):.2f} vs uplifting={np.mean(upl):.2f}"
    )


def test_manga_arc_dims_carry_signal(manga_corpus):
    for dim in ("emotional_trajectory", "ending_valence"):
        vals = np.array([b["scores"][dim] for b in manga_corpus.values()])
        assert vals.std() > 0.15, f"{dim} too little spread across manga (std={vals.std():.2f})"
