"""Anime recommendation behavior via the real preference-vector logic."""

import pytest

from tests._helpers import ANIME_CLUSTERS, preference_recommend, present, score_of


def _overlap(titles, cluster_titles):
    s = set(cluster_titles)
    return sum(1 for t in titles if t in s)


def test_liking_devastation_anime_surfaces_dark(anime_corpus):
    likes = [(t, 5) for t in present(anime_corpus, ANIME_CLUSTERS["devastation"])[:3]]
    recs = preference_recommend(anime_corpus, likes, k=8)
    assert _overlap(recs, ANIME_CLUSTERS["cozy_wholesome"]) == 0, f"Loving devastation surfaced cozy: {recs}"


def test_liking_cozy_anime_surfaces_wholesome(anime_corpus):
    likes = [(t, 5) for t in present(anime_corpus, ANIME_CLUSTERS["cozy_wholesome"])[:3]]
    recs = preference_recommend(anime_corpus, likes, k=8)
    assert _overlap(recs, ANIME_CLUSTERS["devastation"]) == 0, f"Loving cozy surfaced devastation: {recs}"
    evs = [score_of(anime_corpus, t, "ending_valence") for t in recs]
    assert sum(evs) / len(evs) > 0.45, f"Cozy-loving anime recs not uplifting enough: {evs}"


def test_disliking_dark_anime_pushes_away(anime_corpus):
    likes = [(t, 5) for t in present(anime_corpus, ANIME_CLUSTERS["cozy_wholesome"])[:2]]
    dislike = present(anime_corpus, ANIME_CLUSTERS["dark_psychological"])[:1]
    recs = preference_recommend(anime_corpus, likes + [(dislike[0], 1)], k=5)
    assert _overlap(recs, ANIME_CLUSTERS["dark_psychological"]) == 0, f"Disliked dark still appears: {recs}"
