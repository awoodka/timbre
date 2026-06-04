"""Per-anime scoring sanity — dominant/absent emotions + sparsity."""

import pytest

from tests._helpers import ANIME_EXPECTED_DOMINANT, ANIME_EXPECTED_ABSENT, top_dims


@pytest.mark.parametrize("title,dim,k", ANIME_EXPECTED_DOMINANT)
def test_anime_expected_dominant_present(anime_corpus, title, dim, k):
    if title not in anime_corpus:
        pytest.skip(f"{title} not in anime corpus")
    td = top_dims(anime_corpus, title, k)
    assert dim in td, f"{title}: expected '{dim}' among top {k}, got {td}."


@pytest.mark.parametrize("title,dim,k", ANIME_EXPECTED_ABSENT)
def test_anime_inflation_guard(anime_corpus, title, dim, k):
    if title not in anime_corpus:
        pytest.skip(f"{title} not in anime corpus")
    td = top_dims(anime_corpus, title, k)
    assert dim not in td, f"{title}: '{dim}' should NOT be among top {k}, got {td}."


def test_anime_scores_in_unit_range(anime_corpus):
    for title, b in anime_corpus.items():
        for dim, v in b["scores"].items():
            assert 0.0 <= v <= 1.0, f"{title}.{dim}={v} out of [0,1]"


def test_anime_are_sparse(anime_corpus):
    offenders = {t: n for t, b in anime_corpus.items()
                 if (n := sum(1 for v in b["scores"].values() if v >= 0.5)) > 12}
    assert not offenders, f"Anime with >12 dims >=0.5: {offenders}"
