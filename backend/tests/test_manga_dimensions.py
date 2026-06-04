"""Per-manga scoring sanity — dominant/absent emotions + sparsity."""

import pytest

from tests._helpers import MANGA_EXPECTED_DOMINANT, MANGA_EXPECTED_ABSENT, top_dims


@pytest.mark.parametrize("title,dim,k", MANGA_EXPECTED_DOMINANT)
def test_manga_expected_dominant_present(manga_corpus, title, dim, k):
    if title not in manga_corpus:
        pytest.skip(f"{title} not in manga corpus")
    td = top_dims(manga_corpus, title, k)
    assert dim in td, f"{title}: expected '{dim}' among top {k}, got {td}."


@pytest.mark.parametrize("title,dim,k", MANGA_EXPECTED_ABSENT)
def test_manga_inflation_guard(manga_corpus, title, dim, k):
    if title not in manga_corpus:
        pytest.skip(f"{title} not in manga corpus")
    td = top_dims(manga_corpus, title, k)
    assert dim not in td, f"{title}: '{dim}' should NOT be among top {k}, got {td}."


def test_manga_scores_in_unit_range(manga_corpus):
    for title, b in manga_corpus.items():
        for dim, v in b["scores"].items():
            assert 0.0 <= v <= 1.0, f"{title}.{dim}={v} out of [0,1]"


def test_manga_are_sparse(manga_corpus):
    offenders = {t: n for t, b in manga_corpus.items()
                 if (n := sum(1 for v in b["scores"].values() if v >= 0.5)) > 12}
    assert not offenders, f"Manga with >12 dims >=0.5: {offenders}"
