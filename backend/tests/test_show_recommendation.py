"""TV-show recommendation behavior via the real preference-vector logic, on shows.
Mirrors test_film_recommendation."""

import pytest

from tests._helpers import SHOW_CLUSTERS, preference_recommend, present, score_of


def _overlap(titles, cluster_titles):
    s = set(cluster_titles)
    return sum(1 for t in titles if t in s)


def test_liking_devastation_shows_surfaces_dark(show_corpus):
    likes = [(t, 5) for t in present(show_corpus, SHOW_CLUSTERS["devastation"])[:3]]
    recs = preference_recommend(show_corpus, likes, k=8)
    assert _overlap(recs, SHOW_CLUSTERS["cozy_uplifting"]) == 0, f"Loving devastation surfaced cozy shows: {recs}"
    evs = [score_of(show_corpus, t, "ending_valence") for t in recs]
    assert sum(evs) / len(evs) < 0.50, f"Dark-loving show recs not bleak enough: {evs}"


def test_liking_cozy_shows_surfaces_uplifting(show_corpus):
    likes = [(t, 5) for t in present(show_corpus, SHOW_CLUSTERS["cozy_uplifting"])[:3]]
    recs = preference_recommend(show_corpus, likes, k=8)
    assert _overlap(recs, SHOW_CLUSTERS["devastation"]) == 0, f"Loving cozy surfaced devastation: {recs}"
    evs = [score_of(show_corpus, t, "ending_valence") for t in recs]
    assert sum(evs) / len(evs) > 0.50, f"Cozy-loving show recs not uplifting enough: {evs}"


def test_disliking_horror_shows_pushes_away(show_corpus):
    likes = [(t, 5) for t in present(show_corpus, SHOW_CLUSTERS["cozy_uplifting"])[:2]]
    dislike = present(show_corpus, SHOW_CLUSTERS["horror_dread"])[:1]
    recs = preference_recommend(show_corpus, likes + [(dislike[0], 1)], k=5)
    assert _overlap(recs, SHOW_CLUSTERS["horror_dread"]) == 0, f"Disliked horror still appears: {recs}"


def test_show_mixed_taste_resolves_coherently(show_corpus):
    likes = [(t, 5) for t in present(show_corpus, SHOW_CLUSTERS["melancholy_longing"])[:3]]
    hates = [(t, 1) for t in present(show_corpus, SHOW_CLUSTERS["horror_dread"])[:2]]
    recs = preference_recommend(show_corpus, likes + hates, k=8)
    assert _overlap(recs, SHOW_CLUSTERS["horror_dread"]) == 0, f"Hated horror still surfaced: {recs}"
