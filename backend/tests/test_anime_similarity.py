"""Anime emotional similarity — cluster cohesion/separation + ordered triplets."""

import pytest

from tests._helpers import ANIME_CLUSTERS, mean_within_sim, mean_cross_sim, sim, present

_DARK = ["devastation", "dark_psychological", "melancholy_contemplative"]


@pytest.mark.parametrize("cluster", list(ANIME_CLUSTERS))
def test_anime_cluster_is_cohesive(anime_corpus, cluster):
    within = mean_within_sim(anime_corpus, ANIME_CLUSTERS[cluster])
    members = set(present(anime_corpus, ANIME_CLUSTERS[cluster]))
    others = [t for t in anime_corpus if t not in members]
    baseline = mean_cross_sim(anime_corpus, list(members), others)
    assert within > baseline + 0.05, (
        f"Anime cluster '{cluster}' not cohesive: within={within:.3f} vs baseline={baseline:.3f}"
    )


@pytest.mark.parametrize("dark", _DARK)
def test_anime_dark_separates_from_cozy(anime_corpus, dark):
    within = mean_within_sim(anime_corpus, ANIME_CLUSTERS[dark])
    cross = mean_cross_sim(anime_corpus, ANIME_CLUSTERS[dark], ANIME_CLUSTERS["cozy_wholesome"])
    assert within > cross, f"'{dark}' anime not separated from cozy: within={within:.3f} <= cross={cross:.3f}"


ANIME_ORDERED_TRIPLETS = [
    ("Berserk", "Attack on Titan", "K-On!", "dark fantasy dread over cozy"),
    ("Your Lie in April", "Clannad: After Story", "One Punch Man", "tragedy over comedy"),
    ("Monster", "Death Note", "Spy x Family", "psychological dread over wholesome"),
    ("K-On!", "Barakamon", "Berserk", "cozy over dread"),
    ("Cowboy Bebop", "Mushishi", "Demon Slayer", "melancholic contemplation over action"),
    ("Fullmetal Alchemist: Brotherhood", "Hunter x Hunter", "Higurashi When They Cry", "adventure over horror"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", ANIME_ORDERED_TRIPLETS)
def test_anime_emotional_ordering_beats_genre(anime_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in anime_corpus:
            pytest.skip(f"{t} not in anime corpus")
    s_close, s_far = sim(anime_corpus, anchor, closer), sim(anime_corpus, anchor, farther)
    assert s_close > s_far, f"{anchor}: closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."


ANIME_SUBTLE_TRIPLETS = [
    ("Made in Abyss", "Berserk", "K-On!", "wonder+body-horror nearer dark than cozy (sanity)"),
    ("Neon Genesis Evangelion", "Monster", "Gurren Lagann", "Eva's dread/alienation nearer psychological than triumphant mecha"),
    ("Vinland Saga", "Berserk", "Barakamon", "historical violence/grief nearer dark than cozy"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", ANIME_SUBTLE_TRIPLETS)
def test_anime_subtle_ordering(anime_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in anime_corpus:
            pytest.skip(f"{t} not in anime corpus")
    s_close, s_far = sim(anime_corpus, anchor, closer), sim(anime_corpus, anchor, farther)
    assert s_close > s_far, f"{anchor}: closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."
