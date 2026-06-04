"""Per-show scoring sanity — dominant/absent emotions vs consensus + sparsity.
Mirrors test_film_dimensions on shows."""

import pytest

from tests._helpers import SHOW_EXPECTED_DOMINANT, SHOW_EXPECTED_ABSENT, top_dims


@pytest.mark.parametrize("title,dim,k", SHOW_EXPECTED_DOMINANT)
def test_show_expected_dominant_present(show_corpus, title, dim, k):
    if title not in show_corpus:
        pytest.skip(f"{title} not in show corpus")
    td = top_dims(show_corpus, title, k)
    assert dim in td, f"{title}: expected '{dim}' among top {k} (consensus), got {td}."


@pytest.mark.parametrize("title,dim,k", SHOW_EXPECTED_ABSENT)
def test_show_inflation_guard(show_corpus, title, dim, k):
    if title not in show_corpus:
        pytest.skip(f"{title} not in show corpus")
    td = top_dims(show_corpus, title, k)
    assert dim not in td, f"{title}: '{dim}' should NOT be among top {k} (inflation?), got {td}."


def test_show_scores_in_unit_range(show_corpus):
    for title, b in show_corpus.items():
        for dim, v in b["scores"].items():
            assert 0.0 <= v <= 1.0, f"{title}.{dim}={v} out of [0,1]"


def test_shows_are_sparse(show_corpus):
    offenders = {t: n for t, b in show_corpus.items()
                 if (n := sum(1 for v in b["scores"].values() if v >= 0.5)) > 12}
    assert not offenders, f"Shows with >12 dimensions >=0.5 (insufficiently sparse): {offenders}"
