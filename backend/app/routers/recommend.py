from datetime import datetime, timezone

import numpy as np
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_optional_user
from app.database import get_db
from app.dimensions import DIMENSION_KEYS, EMOTIONAL_DIMENSIONS, NUM_DIMENSIONS
from app.models.media import MediaItem
from app.models.user import Rating, User
from app.schemas import (
    MediaResponse,
    MediaSimilarResponse,
    ReasonOut,
    RecommendRequest,
    RecommendResponse,
)
from app.services.affinity import build_affinity, confidence, genres_of, rerank
from app.services.feedback import build_taste_profile
from app.services.mood import blend_vectors, build_mood_vector
from app.services.query_parse import parse_query

router = APIRouter(prefix="/api", tags=["recommendations"])

# How many works a user must log before the PURE-TASTE recommender unlocks.
# Experience search (a mood and/or a non-"any" ending) is NOT gated.
MIN_LOGGED_WORKS = 4
# Natural-language search leans mostly on the parsed query, lightly on saved taste.
NL_ALPHA = 0.8
# A liked/sought emotion is a "reason" for a rec if the work scores at least this raw.
REASON_THRESHOLD = 0.5

# Enjoyment re-rank (PURE-TASTE recs only). After retrieving the emotionally-nearest
# candidates, gently float up the media/creators/genres the user tends to ENJOY. The
# tilt is bounded by ±ENJOY_LAMBDA and confidence-scaled, so emotion stays the core
# (retrieval + the dominant term). See services/affinity.py.
ENJOY_LAMBDA = 0.08
RERANK_POOL = 50  # emotional candidates to consider before the gentle re-rank

# Experience search — soft ending lean. We don't hard-filter on how a work ends;
# instead the ranking subtracts a small penalty proportional to the distance between
# a work's raw ending_valence and the requested tone's target, so results *lean*
# toward that landing without excluding strong mood/taste matches.
LAMBDA_END = 0.25
ENDING_TARGETS = {"bleak": 0.15, "bittersweet": 0.5, "uplifting": 0.85}
# A result earns an "ends …" reason only when it genuinely lands in that band.
ENDING_BANDS = {  # [lo, hi) on raw ending_valence
    "bleak": (-0.01, 0.4),
    "bittersweet": (0.4, 0.6),
    "uplifting": (0.6, 1.01),
}
ENDING_REASON_NAME = {
    "bleak": "ends bleak",
    "bittersweet": "bittersweet ending",
    "uplifting": "ends uplifting",
}

_NAME = {d["key"]: d["name"] for d in EMOTIONAL_DIMENSIONS}
# Raw ending_valence, coalesced to neutral for any malformed/missing breakdown.
_EV = "COALESCE((emotion_breakdown->>'ending_valence')::float, 0.5)"

# Anonymous natural-language (Gemini) searches are free up to FREE_ANON_NL per IP per
# day, then we ask for sign-up. Soft cost guard: in-memory ⇒ per-worker + resets on
# restart — fine at friends-scale; move to a shared store (DB/Redis) to make it exact.
FREE_ANON_NL = 3
_anon_nl: dict[str, tuple[str, int]] = {}  # ip -> (date_str, count)


def _client_ip(request: Request) -> str:
    """Best-effort client IP — prefers Cloudflare / proxy headers, falls back to peer."""
    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _anon_nl_over_cap(ip: str) -> bool:
    """Count one anon NL search for `ip` today; True once it exceeds FREE_ANON_NL."""
    today = datetime.now(timezone.utc).date().isoformat()
    day, count = _anon_nl.get(ip, (today, 0))
    if day != today:
        count = 0
    count += 1
    _anon_nl[ip] = (today, count)
    return count > FREE_ANON_NL


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_media(
    req: RecommendRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """Recommend works by emotional fit. Two modes share this endpoint:

    - **Pure taste** (default body): rank the corpus against the user's aggregated
      per-emotion taste profile. Gated until MIN_LOGGED_WORKS works are logged.
    - **Experience search** (a `mood` map and/or a non-"any" `ending`): the user
      composes the experience they want — feelings to seek/avoid + how it lands —
      blended with their taste by the `alpha` dial. Ungated: it works with zero
      ratings (pure mood) and taste blends in automatically once available.

    Both rank with the same pgvector cosine over standardized (mean-centered)
    vectors; experience search additionally leans the result toward the requested
    ending via a soft penalty on each work's raw ending_valence.
    """
    rows = [] if user is None else list(await db.scalars(select(Rating).where(Rating.user_id == user.id)))

    # Anonymous free-text (Gemini) searches are free up to FREE_ANON_NL/day per IP,
    # then we ask them to sign up — protects the API key + nudges accounts.
    if user is None and req.description and _anon_nl_over_cap(_client_ip(request)):
        return RecommendResponse(signup_required=True)

    # Natural-language search: parse the free-text description into the same
    # structured query the composer produces (feelings to seek/avoid, an ending,
    # an optional medium), leaning toward the query over saved taste (NL_ALPHA).
    mood, ending, medium, alpha = req.mood, req.ending, req.medium, req.alpha
    if req.description:
        parsed = await parse_query(req.description)
        mood, ending, medium, alpha = parsed["mood"], parsed["ending"], parsed["medium"], NL_ALPHA
        if not mood and ending == "any" and not medium:
            # Couldn't read any feeling/intent from the text → honest empty result.
            return RecommendResponse(logged=len(rows), needed=MIN_LOGGED_WORKS)

    is_experience = bool(mood) or ending != "any" or bool(req.description)

    taste = build_taste_profile([r.feedback for r in rows]) if rows else np.zeros(NUM_DIMENSIONS)

    affinity = None
    if not is_experience:
        # ── Pure-taste path (gated) ──
        if len(rows) < MIN_LOGGED_WORKS:
            return RecommendResponse(gated=True, logged=len(rows), needed=MIN_LOGGED_WORKS)
        norm = float(np.linalg.norm(taste))
        if norm == 0.0:
            # Enough works logged, but no usable marks (all neutral / cancelling).
            return RecommendResponse(logged=len(rows), needed=MIN_LOGGED_WORKS)
        query_vec = taste / norm
        liked = {DIMENSION_KEYS[i] for i, w in enumerate(query_vec) if w > 0}
        # Gentle enjoyment tilt on the emotionally-ranked results (pure-taste only),
        # opt-in per user (Settings → "lean toward what I enjoy"); off ⇒ pure emotion.
        if user.settings.get("lean_enjoyment", False):
            affinity = await _enjoyment_affinity(db, user.id)
    else:
        # ── Experience search (ungated) ──
        mood_vec = build_mood_vector(mood or {})
        query_vec = blend_vectors(mood_vec, taste, alpha)
        if float(np.linalg.norm(query_vec)) == 0.0 and ending == "any":
            # No feelings picked and no taste yet → nothing to rank.
            return RecommendResponse(logged=len(rows), needed=MIN_LOGGED_WORKS)
        sought = {DIMENSION_KEYS[i] for i, w in enumerate(mood_vec) if w > 0}
        # Reasons come from the feelings the user asked for; if they leaned only on
        # taste (no seeks), fall back to the blended-positive emotions.
        liked = sought or {DIMENSION_KEYS[i] for i, w in enumerate(query_vec) if w > 0}

    db_rows = await _rank(
        db, query_vec, {str(r.media_id) for r in rows}, ending, req.limit, medium, affinity
    )

    recs = []
    for row in db_rows:
        item = await db.get(MediaItem, row[0])
        bd = item.emotion_breakdown or {}
        reason_keys = sorted(
            (k for k in liked if bd.get(k, 0) >= REASON_THRESHOLD),
            key=lambda k: -bd.get(k, 0.0),
        )[:3]
        reasons = [ReasonOut(key=k, name=_NAME.get(k, k)) for k in reason_keys]
        # Truthful ending reason: only when the work actually lands in-band.
        if ending != "any":
            lo, hi = ENDING_BANDS[ending]
            if lo <= bd.get("ending_valence", 0.5) < hi:
                reasons.append(
                    ReasonOut(
                        key="ending_valence",
                        name=ENDING_REASON_NAME[ending],
                        kind="ending",
                    )
                )
        recs.append(
            MediaSimilarResponse(
                item=MediaResponse.from_orm_item(item),
                similarity=round(float(row[1]), 4),
                reasons=reasons,
            )
        )

    return RecommendResponse(logged=len(rows), needed=MIN_LOGGED_WORKS, recommendations=recs)


async def _enjoyment_affinity(db, user_id):
    """The signed-in user's enjoyment-by-lane table + confidence, for the re-rank.
    Returns None when there's no usable star signal — so ranking stays pure emotion."""
    q = (
        select(Rating.enjoyment, MediaItem.medium, MediaItem.creator, MediaItem.metadata_)
        .join(MediaItem, Rating.media_id == MediaItem.id)
        .where(Rating.user_id == user_id, Rating.enjoyment.isnot(None))
    )
    rated = [(e, m, c, genres_of(meta)) for (e, m, c, meta) in (await db.execute(q)).all()]
    if not rated:
        return None
    table, overall, n = build_affinity(rated)
    return (table, overall, confidence(n)) if table else None


async def _rank(db, query_vec, rated_ids, ending, limit, medium=None, affinity=None):
    """Rank the corpus by emotional fit, excluding already-rated works.

    The displayed `similarity` is always the pure cosine match. The ORDER BY leans
    toward the requested ending via a soft penalty on raw ending_valence ("any" =
    no lean, i.e. the original pure-cosine ranking). If the query vector is empty
    (ending-only search by a brand-new user), we rank purely by how close each
    work lands to the target ending. An optional `medium` restricts the candidate
    set to one medium (powers per-medium "Beyond books" rows).

    `affinity` (pure-taste recs only): when given as (table, overall, conf), retrieve
    a larger pool by emotion and gently re-rank it by enjoyment (bounded by
    ENJOY_LAMBDA). Retrieval stays purely emotional and the returned `similarity`
    stays the cosine. None ⇒ the original one-shot cosine ranking, unchanged.
    """
    params = {"lim": max(limit * 3, RERANK_POOL) if affinity else limit}
    exclude = ""
    if rated_ids:
        placeholders = ", ".join(f"'{rid}'" for rid in rated_ids)
        exclude = f"AND id NOT IN ({placeholders})"

    medium_clause = ""
    if medium:
        params["medium"] = medium
        medium_clause = "AND medium = :medium"

    zero_query = float(np.linalg.norm(query_vec)) == 0.0

    if zero_query:
        # Ending-only (no feelings, no taste): order by closeness to the ending.
        params["target"] = ENDING_TARGETS[ending]
        select_sim = f"1 - abs({_EV} - :target)"
        order_by = f"abs({_EV} - :target) ASC"
    else:
        params["vec"] = "[" + ",".join(str(v) for v in query_vec.tolist()) + "]"
        select_sim = "1 - (emotion_vector <=> CAST(:vec AS vector))"
        if ending == "any":
            order_by = "emotion_vector <=> CAST(:vec AS vector) ASC"
        else:
            params["lam"] = LAMBDA_END
            params["target"] = ENDING_TARGETS[ending]
            order_by = (
                f"((1 - (emotion_vector <=> CAST(:vec AS vector))) "
                f"- :lam * abs({_EV} - :target)) DESC"
            )

    cols = f"id, {select_sim} AS similarity"
    if affinity:
        cols += ", medium, creator, metadata"
    query = text(
        f"""
        SELECT {cols}
        FROM media
        WHERE emotion_vector IS NOT NULL {exclude} {medium_clause}
        ORDER BY {order_by}
        LIMIT :lim
        """
    )
    result = (await db.execute(query, params)).fetchall()
    if not affinity:
        return result
    # Gentle, bounded enjoyment re-rank over the emotionally-retrieved pool.
    table, overall, conf = affinity
    candidates = [(r[0], float(r[1]), r[2], r[3], genres_of(r[4])) for r in result]
    return rerank(candidates, table, overall, conf, ENJOY_LAMBDA)[:limit]
