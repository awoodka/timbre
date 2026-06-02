"""The arc dimensions: do trajectory/ending_valence carry correct, useful signal?

This is the feature added to separate works that share a dominant emotion but
differ in how they resolve (e.g. tragic vs. redemptive despair). Ground truth +
sources (saddest- vs happiest-ending lists): tests/_helpers.py.
"""

import numpy as np
import pytest

from tests._helpers import ARC_TRAGIC, ARC_UPLIFTING, sim, score_of, present


@pytest.mark.parametrize("title", ARC_TRAGIC)
def test_tragic_books_have_low_ending_valence(corpus, title):
    if title not in corpus:
        pytest.skip(f"{title} not in corpus")
    ev = score_of(corpus, title, "ending_valence")
    assert ev <= 0.35, (
        f"{title} has a bleak/tragic ending per consensus but ending_valence={ev:.2f} "
        "(should be low). Scorer is under-reading the bleakness of the ending."
    )


@pytest.mark.parametrize("title", ARC_UPLIFTING)
def test_uplifting_books_have_high_ending_valence(corpus, title):
    if title not in corpus:
        pytest.skip(f"{title} not in corpus")
    ev = score_of(corpus, title, "ending_valence")
    assert ev >= 0.60, (
        f"{title} has an uplifting/redemptive ending per consensus but "
        f"ending_valence={ev:.2f} (should be high)."
    )


def test_ending_valence_separates_tragic_from_uplifting(corpus):
    """Aggregate sanity: tragic endings should score well below uplifting ones."""
    trag = [score_of(corpus, t, "ending_valence") for t in present(corpus, ARC_TRAGIC)]
    upl = [score_of(corpus, t, "ending_valence") for t in present(corpus, ARC_UPLIFTING)]
    assert np.mean(trag) + 0.30 < np.mean(upl), (
        f"ending_valence not separating arcs: tragic mean={np.mean(trag):.2f} vs "
        f"uplifting mean={np.mean(upl):.2f}"
    )


def test_arc_dimensions_carry_signal(corpus):
    """Arc dims must vary across the corpus (not be near-constant)."""
    for dim in ("emotional_trajectory", "ending_valence"):
        vals = np.array([b["scores"][dim] for b in corpus.values()])
        assert vals.std() > 0.15, f"{dim} has too little spread (std={vals.std():.2f})"


def test_arc_separates_same_emotion_different_resolution(corpus):
    """Works sharing dread+grief but differing in arc should be less similar than
    two equally-bleak ones. The Road & Blood Meridian are both bleak (low arc);
    Beloved shares the grief/dread but resolves (high catharsis/trajectory)."""
    for t in ("The Road", "Blood Meridian", "Beloved"):
        if t not in corpus:
            pytest.skip(f"{t} not in corpus")
    bleak_pair = sim(corpus, "The Road", "Blood Meridian")
    arc_diff = sim(corpus, "The Road", "Beloved")
    assert bleak_pair > arc_diff, (
        f"Arc not separating same-emotion works: sim(Road,BloodMeridian)={bleak_pair:.3f} "
        f"should exceed sim(Road,Beloved)={arc_diff:.3f} (Beloved resolves; the others don't)."
    )


def test_despair_pair_separated_by_ending(corpus):
    """Regression guard for the motivating case: two grief-dominant books with
    different endings (A Little Life = tragic, The Book Thief = bittersweet) must
    not be near-identical."""
    for t in ("A Little Life", "The Book Thief"):
        if t not in corpus:
            pytest.skip(f"{t} not in corpus")
    s = sim(corpus, "A Little Life", "The Book Thief")
    assert s < 0.65, (
        f"A Little Life vs The Book Thief = {s:.3f}; despite shared grief, differing "
        "endings should keep them apart."
    )
