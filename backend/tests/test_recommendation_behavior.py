"""End-to-end recommendation behavior via the real preference-vector logic.

Cluster-based (robust) rather than exact-title: liking a mood should surface
that mood; disliking it should push away; mixed tastes should resolve coherently.
"""

import pytest

from tests._helpers import (
    CLUSTERS, preference_recommend, present, score_of,
)


def _overlap(titles, cluster_titles):
    s = set(cluster_titles)
    return sum(1 for t in titles if t in s)


def test_liking_devastation_surfaces_dark_not_cozy(corpus):
    likes = [(t, 5) for t in present(corpus, CLUSTERS["devastation"])[:3]]
    recs = preference_recommend(corpus, likes, k=8)
    cozy = _overlap(recs, CLUSTERS["cozy_uplifting"])
    assert cozy == 0, f"Loving devastation surfaced cozy/uplifting books: {recs}"
    # Mean ending_valence of recs should skew bleak.
    evs = [score_of(corpus, t, "ending_valence") for t in recs]
    assert sum(evs) / len(evs) < 0.40, f"Dark-loving recs not bleak enough: {evs}"


def test_liking_cozy_surfaces_uplifting_not_devastation(corpus):
    likes = [(t, 5) for t in present(corpus, CLUSTERS["cozy_uplifting"])[:3]]
    recs = preference_recommend(corpus, likes, k=8)
    assert _overlap(recs, CLUSTERS["devastation"]) == 0, (
        f"Loving cozy/uplifting surfaced devastation: {recs}"
    )
    evs = [score_of(corpus, t, "ending_valence") for t in recs]
    assert sum(evs) / len(evs) > 0.55, f"Cozy-loving recs not uplifting enough: {evs}"


def test_disliking_a_mood_pushes_recs_away_from_it(corpus):
    """Like cozy, strongly dislike a cosmic-dread book -> no dread books up top."""
    likes = [(t, 5) for t in present(corpus, CLUSTERS["cozy_uplifting"])[:2]]
    dislike = present(corpus, CLUSTERS["cosmic_dread"])[:1]
    ratings = likes + [(dislike[0], 1)]
    recs = preference_recommend(corpus, ratings, k=5)
    assert _overlap(recs, CLUSTERS["cosmic_dread"]) == 0, (
        f"Disliked cosmic-dread but it still appears: {recs}"
    )


def test_low_rating_changes_results(corpus):
    """Adding a 1-star rating should shift the recommendation list."""
    likes = present(corpus, CLUSTERS["melancholy_longing"])[:2]
    base = preference_recommend(corpus, [(t, 5) for t in likes], k=10)
    disliked = present(corpus, CLUSTERS["cozy_uplifting"])[0]
    shifted = preference_recommend(corpus, [(t, 5) for t in likes] + [(disliked, 1)], k=10)
    assert base != shifted, "Adding a 1-star rating did not change recommendations."


def test_mixed_taste_resolves_coherently(corpus):
    """Love melancholy, hate cosmic-dread -> melancholy/longing surfaces, dread doesn't."""
    likes = [(t, 5) for t in present(corpus, CLUSTERS["melancholy_longing"])[:3]]
    hates = [(t, 1) for t in present(corpus, CLUSTERS["cosmic_dread"])[:2]]
    recs = preference_recommend(corpus, likes + hates, k=8)
    assert _overlap(recs, CLUSTERS["cosmic_dread"]) == 0, f"Hated dread still surfaced: {recs}"
