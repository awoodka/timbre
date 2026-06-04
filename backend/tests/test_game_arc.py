"""Video-game arc dimensions — ending_valence vs sourced tragic/uplifting endings.
(Player-controlled pacing makes the `pacing` dim noisier for games.)"""

import numpy as np
import pytest

from tests._helpers import GAME_ARC_TRAGIC, GAME_ARC_UPLIFTING, score_of, present


@pytest.mark.parametrize("title", GAME_ARC_TRAGIC)
def test_game_tragic_low_ending_valence(game_corpus, title):
    if title not in game_corpus:
        pytest.skip(f"{title} not in game corpus")
    ev = score_of(game_corpus, title, "ending_valence")
    assert ev <= 0.40, f"{title} has a bleak ending per consensus but ending_valence={ev:.2f}."


@pytest.mark.parametrize("title", GAME_ARC_UPLIFTING)
def test_game_uplifting_high_ending_valence(game_corpus, title):
    if title not in game_corpus:
        pytest.skip(f"{title} not in game corpus")
    ev = score_of(game_corpus, title, "ending_valence")
    assert ev >= 0.60, f"{title} has an uplifting ending per consensus but ending_valence={ev:.2f}."


def test_game_ending_valence_separates_arcs(game_corpus):
    trag = [score_of(game_corpus, t, "ending_valence") for t in present(game_corpus, GAME_ARC_TRAGIC)]
    upl = [score_of(game_corpus, t, "ending_valence") for t in present(game_corpus, GAME_ARC_UPLIFTING)]
    assert np.mean(trag) + 0.30 < np.mean(upl), (
        f"ending_valence not separating game arcs: tragic={np.mean(trag):.2f} vs uplifting={np.mean(upl):.2f}"
    )


def test_game_arc_dims_carry_signal(game_corpus):
    for dim in ("emotional_trajectory", "ending_valence"):
        vals = np.array([b["scores"][dim] for b in game_corpus.values()])
        assert vals.std() > 0.15, f"{dim} too little spread across games (std={vals.std():.2f})"
