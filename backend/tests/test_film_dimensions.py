"""Per-film scoring sanity — dominant/absent emotions vs consensus + sparsity.
Mirrors test_dimension_validity on films."""

import pytest

from tests._helpers import FILM_EXPECTED_DOMINANT, FILM_EXPECTED_ABSENT, top_dims


@pytest.mark.parametrize("title,dim,k", FILM_EXPECTED_DOMINANT)
def test_film_expected_dominant_present(film_corpus, title, dim, k):
    if title not in film_corpus:
        pytest.skip(f"{title} not in film corpus")
    td = top_dims(film_corpus, title, k)
    assert dim in td, f"{title}: expected '{dim}' among top {k} (consensus), got {td}."


@pytest.mark.parametrize("title,dim,k", FILM_EXPECTED_ABSENT)
def test_film_inflation_guard(film_corpus, title, dim, k):
    if title not in film_corpus:
        pytest.skip(f"{title} not in film corpus")
    td = top_dims(film_corpus, title, k)
    assert dim not in td, f"{title}: '{dim}' should NOT be among top {k} (inflation?), got {td}."


def test_film_scores_in_unit_range(film_corpus):
    for title, b in film_corpus.items():
        for dim, v in b["scores"].items():
            assert 0.0 <= v <= 1.0, f"{title}.{dim}={v} out of [0,1]"


def test_films_are_sparse(film_corpus):
    offenders = {t: n for t, b in film_corpus.items()
                 if (n := sum(1 for v in b["scores"].values() if v >= 0.5)) > 12}
    assert not offenders, f"Films with >12 dimensions >=0.5 (insufficiently sparse): {offenders}"
