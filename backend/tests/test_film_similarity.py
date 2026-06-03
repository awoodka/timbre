"""Film emotional similarity — relative cluster cohesion/separation + ordered
triplets (emotion over genre). Mirrors test_emotional_similarity on films."""

import pytest

from tests._helpers import FILM_CLUSTERS, mean_within_sim, mean_cross_sim, sim, present

_DARK = ["devastation", "horror_dread", "tension_thriller", "melancholy_longing"]


@pytest.mark.parametrize("cluster", list(FILM_CLUSTERS))
def test_film_cluster_is_cohesive(film_corpus, cluster):
    within = mean_within_sim(film_corpus, FILM_CLUSTERS[cluster])
    members = set(present(film_corpus, FILM_CLUSTERS[cluster]))
    others = [t for t in film_corpus if t not in members]
    baseline = mean_cross_sim(film_corpus, list(members), others)
    assert within > baseline + 0.05, (
        f"Film cluster '{cluster}' not cohesive: within={within:.3f} vs baseline={baseline:.3f}"
    )


@pytest.mark.parametrize("dark", _DARK)
def test_film_dark_separates_from_cozy(film_corpus, dark):
    within = mean_within_sim(film_corpus, FILM_CLUSTERS[dark])
    cross = mean_cross_sim(film_corpus, FILM_CLUSTERS[dark], FILM_CLUSTERS["cozy_uplifting"])
    assert within > cross, (
        f"'{dark}' films not separated from cozy/uplifting: within={within:.3f} <= cross={cross:.3f}"
    )


# (anchor, closer, farther, why) — emotion over genre, film examples (sourced).
FILM_ORDERED_TRIPLETS = [
    ("The Thing", "Alien", "Paddington 2",
     "isolated creature-horror dread over cozy comedy"),
    ("Grave of the Fireflies", "Schindler's List", "My Neighbor Totoro",
     "war devastation over cozy — note Grave & Totoro are both Ghibli-era anime, opposite feeling"),
    ("Lost in Translation", "Her", "The Thing",
     "quiet urban longing over creature horror"),
    ("No Country for Old Men", "Se7en", "Amélie",
     "bleak crime dread over whimsy"),
    ("My Neighbor Totoro", "Paddington 2", "Hereditary",
     "warm comfort over dread"),
    ("2001: A Space Odyssey", "Interstellar", "Hereditary",
     "cosmic awe over horror"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", FILM_ORDERED_TRIPLETS)
def test_film_emotional_ordering_beats_genre(film_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in film_corpus:
            pytest.skip(f"{t} not in film corpus")
    s_close, s_far = sim(film_corpus, anchor, closer), sim(film_corpus, anchor, farther)
    assert s_close > s_far, (
        f"{anchor}: expected closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."
    )


# Subtle/adversarial — most likely to reveal mis-scoring.
FILM_SUBTLE_TRIPLETS = [
    ("Annihilation", "The Thing", "2001: A Space Odyssey",
     "sources class Annihilation as cosmic horror; if it fails, it's scored more as awe than dread"),
    ("Solaris", "Her", "The Thing",
     "Tarkovsky's Solaris is melancholic sci-fi — nearer quiet longing than creature horror"),
    ("Dune", "Alien", "Amélie",
     "bleak space epic nearer space-horror than whimsy"),
    ("Children of Men", "Nineteen Eighty-Four", "My Neighbor Totoro",
     "oppressive dystopia over cozy"),
]


@pytest.mark.parametrize("anchor,closer,farther,why", FILM_SUBTLE_TRIPLETS)
def test_film_subtle_ordering(film_corpus, anchor, closer, farther, why):
    for t in (anchor, closer, farther):
        if t not in film_corpus:
            pytest.skip(f"{t} not in film corpus")
    s_close, s_far = sim(film_corpus, anchor, closer), sim(film_corpus, anchor, farther)
    assert s_close > s_far, (
        f"{anchor}: expected closer to '{closer}' ({s_close:.3f}) than '{farther}' ({s_far:.3f}). {why}."
    )
