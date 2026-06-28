"""Enjoyment affinity — a bounded, *secondary* preference signal layered on top of
the emotion-cosine ranking (pure-taste recs only).

It NEVER affects retrieval (which works become candidates) — only the ORDER within
the emotionally-relevant top-K. It is fully decoupled from the emotion feedback, the
derived resonance, and the taste profile (those stay emotion-only). Everything here
is a pure function, so the re-rank is unit-testable offline (no DB).
"""

import json

import numpy as np

# Min starred works in a lane (medium / creator / genre) before we trust its average.
MIN_LANE_DATA = 2
# Number of starred works for FULL confidence in the affinity signal (linear ramp).
ENJOY_CONF_FULL = 8


def genres_of(metadata) -> list[str]:
    """Best-effort genre list from a work's `metadata_` JSON (shape varies by medium,
    and raw-SQL JSON may arrive as a str). Missing/garbled genre → []."""
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            return []
    if isinstance(metadata, dict):
        g = metadata.get("genre")
        if isinstance(g, list):
            return [str(x) for x in g]
        if isinstance(g, str):
            return [g]
    return []


def build_affinity(rated):
    """`rated`: iterable of (enjoyment:int|None, medium, creator, genres:list).

    Returns (table, overall_avg, n_starred):
      - `table`: {"lane:value" → mean star}, kept only when a lane has ≥ MIN_LANE_DATA
        starred works (a single rating can't define a "preference").
      - `overall_avg`: the user's own mean star — their baseline.
      - `n_starred`: how many works they've starred.
    Works without a star contribute nothing.
    """
    starred = [(int(e), m, c, g or []) for (e, m, c, g) in rated if e]
    if not starred:
        return {}, 0.0, 0
    overall = sum(e for e, *_ in starred) / len(starred)
    buckets: dict[str, list[int]] = {}
    for e, medium, creator, genres in starred:
        for k in (f"medium:{medium}", f"creator:{creator}", *(f"genre:{g}" for g in genres)):
            buckets.setdefault(k, []).append(e)
    table = {k: sum(v) / len(v) for k, v in buckets.items() if len(v) >= MIN_LANE_DATA}
    return table, overall, len(starred)


def affinity_score(medium, creator, genres, table, overall) -> float:
    """a(w) ∈ [−1, 1]: how much the user enjoys this work's lanes vs their own
    baseline — mean lane-deviation (avg_star − overall)/2, clamped. 0 when no lane of
    this work has enough data (so an unfamiliar lane is neutral, never penalized)."""
    keys = [f"medium:{medium}", f"creator:{creator}", *(f"genre:{g}" for g in (genres or []))]
    devs = [(table[k] - overall) / 2.0 for k in keys if k in table]
    if not devs:
        return 0.0
    return float(np.clip(sum(devs) / len(devs), -1.0, 1.0))


def confidence(n_starred) -> float:
    """C ∈ [0, 1] — ramps linearly with how many works the user has starred, so a
    sparse signal can't over-steer."""
    return min(1.0, n_starred / ENJOY_CONF_FULL)


def rerank(candidates, table, overall, conf, lam):
    """Re-order emotionally-retrieved candidates by `score = cosine + lam·conf·a(w)`.

    `candidates`: list of (id, cosine, medium, creator, genres). Returns them sorted
    by the blended score (desc), each as (id, cosine) — the cosine is preserved so the
    displayed "match %" stays purely emotional.

    Emotion-forward by construction: the enjoyment term is bounded by ±lam (|a|≤1,
    conf≤1), so a candidate more than `lam` closer in cosine is never displaced; and
    conf == 0 (no stars) or an empty table leaves the order untouched.
    """
    if not table or conf <= 0.0:
        return [(cid, cos) for (cid, cos, *_rest) in candidates]
    scored = []
    for cid, cos, medium, creator, genres in candidates:
        a = affinity_score(medium, creator, genres, table, overall)
        scored.append((cos + lam * conf * a, cid, cos))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [(cid, cos) for (_s, cid, cos) in scored]
