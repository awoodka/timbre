"""Per-book scoring sanity: do dominant dimensions match consensus, and is the
old inflation gone? These isolate *scoring* quality (call #2) from *geometry*.
"""

import pytest

from tests._helpers import EXPECTED_DOMINANT, EXPECTED_ABSENT, top_dims


@pytest.mark.parametrize("title,dim,k", EXPECTED_DOMINANT)
def test_expected_dominant_emotion_present(corpus, title, dim, k):
    if title not in corpus:
        pytest.skip(f"{title} not in corpus")
    td = top_dims(corpus, title, k)
    assert dim in td, (
        f"{title}: expected '{dim}' among top {k} dimensions (consensus), got {td}."
    )


@pytest.mark.parametrize("title,dim,k", EXPECTED_ABSENT)
def test_inflation_guard_emotion_absent(corpus, title, dim, k):
    """Emotions that should NOT dominate (e.g. dread in a cozy book) must stay out
    of the top-k — guards against the pre-fix inflation returning."""
    if title not in corpus:
        pytest.skip(f"{title} not in corpus")
    td = top_dims(corpus, title, k)
    assert dim not in td, (
        f"{title}: '{dim}' should NOT be among top {k} (inflation?), got {td}."
    )


def test_scores_in_unit_range(corpus):
    for title, b in corpus.items():
        for dim, v in b["scores"].items():
            assert 0.0 <= v <= 1.0, f"{title}.{dim}={v} out of [0,1]"


def test_books_are_sparse_not_everything_lights_up(corpus):
    """A well-scored book has a focused profile: only a handful of dimensions
    should be strongly present (>=0.5). Broad high-scoring = the inflation bug."""
    offenders = {}
    for title, b in corpus.items():
        n_high = sum(1 for v in b["scores"].values() if v >= 0.5)
        if n_high > 12:
            offenders[title] = n_high
    assert not offenders, (
        f"Books with >12 dimensions >=0.5 (insufficiently sparse / inflated): {offenders}"
    )
