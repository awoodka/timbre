"""Film recommendation behavior via the real preference-vector logic, on films.
Mirrors test_recommendation_behavior."""

import pytest

from tests._helpers import FILM_CLUSTERS, preference_recommend, present, score_of


def _overlap(titles, cluster_titles):
    s = set(cluster_titles)
    return sum(1 for t in titles if t in s)


def test_liking_devastation_films_surfaces_dark(film_corpus):
    likes = [(t, 5) for t in present(film_corpus, FILM_CLUSTERS["devastation"])[:3]]
    recs = preference_recommend(film_corpus, likes, k=8)
    assert _overlap(recs, FILM_CLUSTERS["cozy_uplifting"]) == 0, f"Loving devastation surfaced cozy films: {recs}"
    evs = [score_of(film_corpus, t, "ending_valence") for t in recs]
    assert sum(evs) / len(evs) < 0.45, f"Dark-loving film recs not bleak enough: {evs}"


def test_liking_cozy_films_surfaces_uplifting(film_corpus):
    likes = [(t, 5) for t in present(film_corpus, FILM_CLUSTERS["cozy_uplifting"])[:3]]
    recs = preference_recommend(film_corpus, likes, k=8)
    assert _overlap(recs, FILM_CLUSTERS["devastation"]) == 0, f"Loving cozy surfaced devastation: {recs}"
    evs = [score_of(film_corpus, t, "ending_valence") for t in recs]
    assert sum(evs) / len(evs) > 0.55, f"Cozy-loving film recs not uplifting enough: {evs}"


def test_disliking_horror_pushes_away(film_corpus):
    likes = [(t, 5) for t in present(film_corpus, FILM_CLUSTERS["cozy_uplifting"])[:2]]
    dislike = present(film_corpus, FILM_CLUSTERS["horror_dread"])[:1]
    recs = preference_recommend(film_corpus, likes + [(dislike[0], 1)], k=5)
    assert _overlap(recs, FILM_CLUSTERS["horror_dread"]) == 0, f"Disliked horror still appears: {recs}"


def test_film_mixed_taste_resolves_coherently(film_corpus):
    likes = [(t, 5) for t in present(film_corpus, FILM_CLUSTERS["melancholy_longing"])[:3]]
    hates = [(t, 1) for t in present(film_corpus, FILM_CLUSTERS["horror_dread"])[:2]]
    recs = preference_recommend(film_corpus, likes + hates, k=8)
    assert _overlap(recs, FILM_CLUSTERS["horror_dread"]) == 0, f"Hated horror still surfaced: {recs}"
