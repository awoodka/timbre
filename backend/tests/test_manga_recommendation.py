"""Manga recommendation behavior via the real preference-vector logic."""

import pytest

from tests._helpers import MANGA_CLUSTERS, preference_recommend, present, score_of


def _overlap(titles, cluster_titles):
    s = set(cluster_titles)
    return sum(1 for t in titles if t in s)


def test_liking_devastation_manga_surfaces_dark(manga_corpus):
    likes = [(t, 5) for t in present(manga_corpus, MANGA_CLUSTERS["devastation"])[:3]]
    recs = preference_recommend(manga_corpus, likes, k=8)
    assert _overlap(recs, MANGA_CLUSTERS["cozy_wholesome"]) == 0, f"Loving devastation surfaced cozy: {recs}"


def test_liking_cozy_manga_surfaces_wholesome(manga_corpus):
    likes = [(t, 5) for t in present(manga_corpus, MANGA_CLUSTERS["cozy_wholesome"])[:3]]
    recs = preference_recommend(manga_corpus, likes, k=8)
    assert _overlap(recs, MANGA_CLUSTERS["devastation"]) == 0, f"Loving cozy surfaced devastation: {recs}"


def test_disliking_horror_manga_pushes_away(manga_corpus):
    likes = [(t, 5) for t in present(manga_corpus, MANGA_CLUSTERS["cozy_wholesome"])[:2]]
    dislike = present(manga_corpus, MANGA_CLUSTERS["horror"])[:1]
    recs = preference_recommend(manga_corpus, likes + [(dislike[0], 1)], k=5)
    assert _overlap(recs, MANGA_CLUSTERS["horror"]) == 0, f"Disliked horror still appears: {recs}"
