"""Manga emotional similarity — cluster cohesion/separation + ordered triplets."""

import pytest

from tests._helpers import MANGA_CLUSTERS, mean_within_sim, mean_cross_sim, sim, present

_DARK = ["devastation", "dark_psychological", "horror", "melancholy_literary"]


@pytest.mark.parametrize("cluster", list(MANGA_CLUSTERS))
def test_manga_cluster_is_cohesive(manga_corpus, cluster):
    within = mean_within_sim(manga_corpus, MANGA_CLUSTERS[cluster])
    members = set(present(manga_corpus, MANGA_CLUSTERS[cluster]))
    others = [t for t in manga_corpus if t not in members]
    baseline = mean_cross_sim(manga_corpus, list(members), others)
    assert within > baseline + 0.05, (
        f"Manga cluster '{cluster}' not cohesive: within={within:.3f} vs baseline={baseline:.3f}"
    )


@pytest.mark.parametrize("dark", _DARK)
def test_manga_dark_separates_from_cozy(manga_corpus, dark):
    within = mean_within_sim(manga_corpus, MANGA_CLUSTERS[dark])
    cross = mean_cross_sim(manga_corpus, MANGA_CLUSTERS[dark], MANGA_CLUSTERS["cozy_wholesome"])
    assert within > cross, f"'{dark}' manga not separated from cozy: within={within:.3f} <= cross={cross:.3f}"


MANGA_ORDERED_TRIPLETS = [
    ("Uzumaki", "Tomie", "Yotsuba&!", "Junji Ito horror over cozy"),
    ("Goodnight Punpun", "Solanin", "One Punch Man", "melancholy over comedy"),
    ("Monster", "Death Note", "Komi Can't Communicate", "psychological dread over wholesome"),
    ("Yotsuba&!", "Barakamon", "Uzumaki", "cozy over horror"),
    ("Vinland Saga", "Vagabond", "Grand Blue", "historical drama over comedy"),
    ("Fullmetal Alchemist", "One Piece", "Homunculus", "adventure over psychological horror"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", MANGA_ORDERED_TRIPLETS)
def test_manga_emotional_ordering_beats_genre(manga_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in manga_corpus:
            pytest.skip(f"{t} not in manga corpus")
    s_close, s_far = sim(manga_corpus, anchor, closer), sim(manga_corpus, anchor, farther)
    assert s_close > s_far, f"{anchor}: closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."


MANGA_SUBTLE_TRIPLETS = [
    ("Berserk", "Attack on Titan", "Fullmetal Alchemist", "Berserk's dread nearer AoT than triumphant FMA"),
    ("A Silent Voice", "Goodnight Punpun", "Demon Slayer", "quiet grief nearer melancholy than action"),
    ("Chainsaw Man", "Tokyo Ghoul", "Yotsuba&!", "dark action-horror over cozy"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", MANGA_SUBTLE_TRIPLETS)
def test_manga_subtle_ordering(manga_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in manga_corpus:
            pytest.skip(f"{t} not in manga corpus")
    s_close, s_far = sim(manga_corpus, anchor, closer), sim(manga_corpus, anchor, farther)
    assert s_close > s_far, f"{anchor}: closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."
