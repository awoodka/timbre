"""TV-show emotional similarity — cluster cohesion/separation + ordered triplets.
Mirrors test_film_similarity on the show corpus."""

import pytest

from tests._helpers import SHOW_CLUSTERS, mean_within_sim, mean_cross_sim, sim, present

_DARK = ["devastation", "horror_dread", "tension_thriller", "melancholy_longing"]


@pytest.mark.parametrize("cluster", list(SHOW_CLUSTERS))
def test_show_cluster_is_cohesive(show_corpus, cluster):
    within = mean_within_sim(show_corpus, SHOW_CLUSTERS[cluster])
    members = set(present(show_corpus, SHOW_CLUSTERS[cluster]))
    others = [t for t in show_corpus if t not in members]
    baseline = mean_cross_sim(show_corpus, list(members), others)
    assert within > baseline + 0.05, (
        f"Show cluster '{cluster}' not cohesive: within={within:.3f} vs baseline={baseline:.3f}"
    )


@pytest.mark.parametrize("dark", _DARK)
def test_show_dark_separates_from_cozy(show_corpus, dark):
    within = mean_within_sim(show_corpus, SHOW_CLUSTERS[dark])
    cross = mean_cross_sim(show_corpus, SHOW_CLUSTERS[dark], SHOW_CLUSTERS["cozy_uplifting"])
    assert within > cross, (
        f"'{dark}' shows not separated from cozy/uplifting: within={within:.3f} <= cross={cross:.3f}"
    )


FILM_ORDERED_TRIPLETS = [
    ("Hannibal", "The Haunting of Hill House", "Ted Lasso",
     "atmospheric horror over cozy comedy"),
    ("Chernobyl", "Band of Brothers", "Schitt's Creek",
     "devastation over cozy comedy"),
    ("BoJack Horseman", "Fleabag", "Hannibal",
     "melancholic introspection over horror"),
    ("Breaking Bad", "The Sopranos", "Bluey",
     "crime tension over a children's comfort show"),
    ("Ted Lasso", "Schitt's Creek", "Chernobyl",
     "warm comfort over devastation"),
    ("Battlestar Galactica", "The Expanse", "Hannibal",
     "sci-fi awe over horror"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", FILM_ORDERED_TRIPLETS)
def test_show_emotional_ordering_beats_genre(show_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in show_corpus:
            pytest.skip(f"{t} not in show corpus")
    s_close, s_far = sim(show_corpus, anchor, closer), sim(show_corpus, anchor, farther)
    assert s_close > s_far, (
        f"{anchor}: expected closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."
    )


# Subtle / adversarial — most likely to reveal mis-scoring.
SHOW_SUBTLE_TRIPLETS = [
    ("Mad Men", "Fleabag", "Breaking Bad",
     "Mad Men's melancholy nearer introspective dramedy than crime tension"),
    ("BoJack Horseman", "After Life", "It's Always Sunny in Philadelphia",
     "melancholic comedy nearer grief-comedy than pure absurdist comedy"),
    ("Stranger Things", "The X-Files", "Ted Lasso",
     "nostalgic genre-dread over cozy (sanity)"),
    ("Severance", "Mr. Robot", "Schitt's Creek",
     "eerie corporate dystopia over cozy comedy"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", SHOW_SUBTLE_TRIPLETS)
def test_show_subtle_ordering(show_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in show_corpus:
            pytest.skip(f"{t} not in show corpus")
    s_close, s_far = sim(show_corpus, anchor, closer), sim(show_corpus, anchor, farther)
    assert s_close > s_far, (
        f"{anchor}: expected closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."
    )
