"""Unit tests for the enjoyment-affinity re-rank (services/affinity.py).

Pure / offline — no DB, no fixtures. Verifies the math and, crucially, the
EMOTION-FORWARD invariants: retrieval is never touched here, the enjoyment tilt is
bounded by lambda, and it self-disables without stars.
"""

import json

from app.services.affinity import (
    ENJOY_CONF_FULL,
    affinity_score,
    build_affinity,
    confidence,
    genres_of,
    rerank,
)

LAM = 0.08


# ---- aggregation ----

def test_build_affinity_aggregates_and_gates_sparse_lanes():
    rated = [
        (5, "film", "Villeneuve", ["Sci-Fi"]),
        (4, "film", "Villeneuve", ["Sci-Fi"]),
        (2, "book", "Anon", ["Drama"]),
    ]
    table, overall, n = build_affinity(rated)
    assert n == 3
    assert abs(overall - (5 + 4 + 2) / 3) < 1e-9
    assert abs(table["medium:film"] - 4.5) < 1e-9       # 2 starred → kept
    assert abs(table["creator:Villeneuve"] - 4.5) < 1e-9
    assert "genre:Sci-Fi" in table
    assert "medium:book" not in table                   # only 1 → below MIN_LANE_DATA
    assert "creator:Anon" not in table


def test_build_affinity_ignores_unstarred():
    rated = [(None, "film", "X", []), (None, "book", "Y", [])]
    assert build_affinity(rated) == ({}, 0.0, 0)


def test_affinity_score_is_signed_deviation_clamped():
    table = {"medium:film": 5.0, "medium:book": 1.0}    # overall 3
    assert affinity_score("film", "Z", [], table, 3.0) == 1.0    # loved lane
    assert affinity_score("book", "Z", [], table, 3.0) == -1.0   # disliked lane
    assert affinity_score("game", "Z", [], table, 3.0) == 0.0    # no data → neutral


def test_confidence_ramps_and_caps():
    assert confidence(0) == 0.0
    assert confidence(ENJOY_CONF_FULL) == 1.0
    assert confidence(ENJOY_CONF_FULL * 2) == 1.0
    assert 0.0 < confidence(ENJOY_CONF_FULL // 2) < 1.0


def test_genres_of_handles_dict_str_json_and_missing():
    assert genres_of({"genre": ["A", "B"]}) == ["A", "B"]
    assert genres_of({"genre": "Solo"}) == ["Solo"]
    assert genres_of({"year": 1999}) == []
    assert genres_of(None) == []
    assert genres_of(json.dumps({"genre": ["J"]})) == ["J"]


# ---- the emotion-forward invariants ----

def _cands():
    # (id, cosine, medium, creator, genres)
    return [
        ("a", 0.90, "book", "P", []),
        ("b", 0.80, "film", "Q", []),
        ("c", 0.50, "film", "Q", []),
    ]


def test_rerank_is_noop_without_stars_or_table():
    base = [("a", 0.90), ("b", 0.80), ("c", 0.50)]
    assert rerank(_cands(), {"medium:film": 5.0}, 3.0, 0.0, LAM) == base   # conf 0
    assert rerank(_cands(), {}, 3.0, 1.0, LAM) == base                     # empty table


def test_rerank_preserves_cosine_for_display():
    out = rerank(_cands(), {"medium:film": 5.0}, 3.0, 1.0, LAM)
    assert dict(out)["b"] == 0.80   # returned value is the cosine, not the blended score


def test_rerank_never_displaces_a_clearly_better_emotional_match():
    # 'a' (neutral) leads 'b' (max-loved film) by 0.10 cosine > lambda=0.08.
    table = {"medium:film": 5.0}    # film deviation +1.0 from overall 3
    out = rerank(_cands(), table, 3.0, 1.0, LAM)
    assert out[0][0] == "a", f"emotion-forward invariant broken: {out}"


def test_rerank_breaks_near_ties_toward_enjoyed_lane():
    cands = [("x", 0.81, "book", "P", []), ("y", 0.80, "film", "Q", [])]
    table = {"medium:film": 5.0}
    out = rerank(cands, table, 3.0, 1.0, LAM)
    assert out[0][0] == "y", f"near-tie not broken toward enjoyed lane: {out}"


def test_rerank_candidate_with_no_lane_data_rides_its_cosine():
    cands = [("a", 0.90, "anime", "Z", []), ("b", 0.80, "film", "Q", [])]
    table = {"medium:film": 5.0}
    out = rerank(cands, table, 3.0, 1.0, LAM)
    assert out[0][0] == "a"   # anime has no affinity → stays on its cosine (0.90 > 0.88)
