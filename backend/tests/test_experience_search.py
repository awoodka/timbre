"""Experience-search recommendation behavior (mood + soft ending lean).

Cluster/relative assertions (robust), mirroring test_recommendation_behavior.py:
composing a mood should surface that mood; the ending dial should lean the mean
ending-valence of the results; the alpha dial should slide mood ↔ taste; rated
works are excluded.
"""

from tests._helpers import CLUSTERS, mood_recommend, present, score_of


def _overlap(titles, cluster):
    s = set(cluster)
    return sum(1 for t in titles if t in s)


def _mean_ev(corpus, titles):
    return sum(score_of(corpus, t, "ending_valence") for t in titles) / len(titles)


def test_cozy_mood_surfaces_cozy_not_devastation(corpus):
    recs = mood_recommend(
        corpus,
        seek=["warmth", "serenity", "hope", "intimacy"],
        avoid=["dread", "tension", "grief"],
        k=8,
    )
    assert _overlap(recs, CLUSTERS["cozy_uplifting"]) > 0, f"cozy mood missed cozy works: {recs}"
    assert _overlap(recs, CLUSTERS["devastation"]) == 0, f"cozy mood surfaced devastation: {recs}"


def test_uplifting_ending_lifts_mean_valence(corpus):
    base = mood_recommend(corpus, seek=["warmth", "hope"], ending="any", k=8)
    lifted = mood_recommend(corpus, seek=["warmth", "hope"], ending="uplifting", k=8)
    assert _mean_ev(corpus, lifted) >= _mean_ev(corpus, base)


def test_bleak_ending_lowers_mean_valence(corpus):
    base = mood_recommend(corpus, seek=["melancholy", "isolation"], ending="any", k=8)
    bleak = mood_recommend(corpus, seek=["melancholy", "isolation"], ending="bleak", k=8)
    assert _mean_ev(corpus, bleak) <= _mean_ev(corpus, base)


def test_alpha_slides_mood_toward_taste(corpus):
    """Seek cozy, but taste = devastation-lovers. alpha=1 → cozy (ends happy);
    alpha=0 → dark taste (ends bleak)."""
    dark_likes = [(t, 5) for t in present(corpus, CLUSTERS["devastation"])[:4]]
    mood_end = mood_recommend(corpus, seek=["warmth", "serenity", "hope"], ratings=dark_likes, alpha=1.0, k=8)
    taste_end = mood_recommend(corpus, seek=["warmth", "serenity", "hope"], ratings=dark_likes, alpha=0.0, k=8)
    assert _mean_ev(corpus, mood_end) > _mean_ev(corpus, taste_end)


def test_excludes_rated_works(corpus):
    dark_likes = [(t, 5) for t in present(corpus, CLUSTERS["devastation"])[:4]]
    recs = mood_recommend(corpus, seek=["melancholy"], ratings=dark_likes, k=20)
    for title, _ in dark_likes:
        assert title not in recs, f"rated work {title} leaked into recs"
