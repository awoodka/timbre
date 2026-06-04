"""Per-game scoring sanity — dominant/absent emotions + sparsity."""

import pytest

from tests._helpers import GAME_EXPECTED_DOMINANT, GAME_EXPECTED_ABSENT, top_dims


@pytest.mark.parametrize("title,dim,k", GAME_EXPECTED_DOMINANT)
def test_game_expected_dominant_present(game_corpus, title, dim, k):
    if title not in game_corpus:
        pytest.skip(f"{title} not in game corpus")
    td = top_dims(game_corpus, title, k)
    assert dim in td, f"{title}: expected '{dim}' among top {k}, got {td}."


@pytest.mark.parametrize("title,dim,k", GAME_EXPECTED_ABSENT)
def test_game_inflation_guard(game_corpus, title, dim, k):
    if title not in game_corpus:
        pytest.skip(f"{title} not in game corpus")
    td = top_dims(game_corpus, title, k)
    assert dim not in td, f"{title}: '{dim}' should NOT be among top {k}, got {td}."


def test_game_scores_in_unit_range(game_corpus):
    for title, b in game_corpus.items():
        for dim, v in b["scores"].items():
            assert 0.0 <= v <= 1.0, f"{title}.{dim}={v} out of [0,1]"


def test_games_are_sparse(game_corpus):
    offenders = {t: n for t, b in game_corpus.items()
                 if (n := sum(1 for v in b["scores"].values() if v >= 0.5)) > 12}
    assert not offenders, f"Games with >12 dims >=0.5: {offenders}"
