"""Video-game recommendation behavior via the real preference-vector logic."""

import pytest

from tests._helpers import GAME_CLUSTERS, preference_recommend, present, score_of


def _overlap(titles, cluster_titles):
    s = set(cluster_titles)
    return sum(1 for t in titles if t in s)


def test_liking_devastation_games_surfaces_dark(game_corpus):
    likes = [(t, 5) for t in present(game_corpus, GAME_CLUSTERS["devastation"])[:3]]
    recs = preference_recommend(game_corpus, likes, k=8)
    assert _overlap(recs, GAME_CLUSTERS["cozy_wholesome"]) == 0, f"Loving devastation surfaced cozy: {recs}"


def test_liking_cozy_games_surfaces_wholesome(game_corpus):
    likes = [(t, 5) for t in present(game_corpus, GAME_CLUSTERS["cozy_wholesome"])[:3]]
    recs = preference_recommend(game_corpus, likes, k=8)
    assert _overlap(recs, GAME_CLUSTERS["devastation"]) == 0, f"Loving cozy surfaced devastation: {recs}"


def test_disliking_horror_games_pushes_away(game_corpus):
    likes = [(t, 5) for t in present(game_corpus, GAME_CLUSTERS["cozy_wholesome"])[:2]]
    dislike = present(game_corpus, GAME_CLUSTERS["horror_dread"])[:1]
    recs = preference_recommend(game_corpus, likes + [(dislike[0], 1)], k=5)
    assert _overlap(recs, GAME_CLUSTERS["horror_dread"]) == 0, f"Disliked horror still appears: {recs}"
