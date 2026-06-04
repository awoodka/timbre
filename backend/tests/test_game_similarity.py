"""Video-game emotional similarity — cluster cohesion/separation + ordered triplets."""

import pytest

from tests._helpers import GAME_CLUSTERS, mean_within_sim, mean_cross_sim, sim, present

_DARK = ["devastation", "horror_dread", "melancholy_contemplative", "dark_oppressive"]


@pytest.mark.parametrize("cluster", list(GAME_CLUSTERS))
def test_game_cluster_is_cohesive(game_corpus, cluster):
    within = mean_within_sim(game_corpus, GAME_CLUSTERS[cluster])
    members = set(present(game_corpus, GAME_CLUSTERS[cluster]))
    others = [t for t in game_corpus if t not in members]
    baseline = mean_cross_sim(game_corpus, list(members), others)
    assert within > baseline + 0.05, (
        f"Game cluster '{cluster}' not cohesive: within={within:.3f} vs baseline={baseline:.3f}"
    )


@pytest.mark.parametrize("dark", _DARK)
def test_game_dark_separates_from_cozy(game_corpus, dark):
    within = mean_within_sim(game_corpus, GAME_CLUSTERS[dark])
    cross = mean_cross_sim(game_corpus, GAME_CLUSTERS[dark], GAME_CLUSTERS["cozy_wholesome"])
    assert within > cross, f"'{dark}' games not separated from cozy: within={within:.3f} <= cross={cross:.3f}"


GAME_ORDERED_TRIPLETS = [
    ("Silent Hill 2", "Amnesia: The Dark Descent", "Stardew Valley", "horror over cozy"),
    ("The Last of Us", "Red Dead Redemption 2", "Animal Crossing: New Horizons", "devastation over cozy"),
    ("Disco Elysium", "Hollow Knight", "Doom Eternal", "melancholic contemplation over action-triumph"),
    ("Stardew Valley", "Animal Crossing: New Horizons", "Silent Hill 2", "cozy over horror"),
    ("Outer Wilds", "Journey", "Outlast", "wonder/awe over horror"),
    ("Celeste", "Hades", "Amnesia: The Dark Descent", "triumph over dread"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", GAME_ORDERED_TRIPLETS)
def test_game_emotional_ordering_beats_genre(game_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in game_corpus:
            pytest.skip(f"{t} not in game corpus")
    s_close, s_far = sim(game_corpus, anchor, closer), sim(game_corpus, anchor, farther)
    assert s_close > s_far, f"{anchor}: closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."


GAME_SUBTLE_TRIPLETS = [
    ("NieR: Automata", "Disco Elysium", "Doom Eternal", "NieR's melancholy nearer existential RPG than action shooter"),
    ("Spiritfarer", "A Short Hike", "Spec Ops: The Line", "grief-but-warm nearer cozy than bleak war"),
    ("Dark Souls", "Bloodborne", "Stardew Valley", "oppressive dread over cozy"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", GAME_SUBTLE_TRIPLETS)
def test_game_subtle_ordering(game_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in game_corpus:
            pytest.skip(f"{t} not in game corpus")
    s_close, s_far = sim(game_corpus, anchor, closer), sim(game_corpus, anchor, farther)
    assert s_close > s_far, f"{anchor}: closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."
