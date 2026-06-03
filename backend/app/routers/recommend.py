import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.media import MediaItem
from app.schemas import MediaResponse, MediaSimilarResponse, RecommendRequest

router = APIRouter(prefix="/api", tags=["recommendations"])

# Rating midpoint: ratings above this pull toward, below push away
RATING_MIDPOINT = 2.5


def build_preference_vector(
    vectors: list[np.ndarray], ratings: list[float]
) -> np.ndarray:
    """
    Build an emotional preference direction from rated books.

    The stored vectors are STANDARDIZED (mean-centered against the corpus centroid),
    so the natural blend is a signed weighted sum around the rating midpoint (2.5):
      1 → -1.5   2 → -0.5   3 → +0.5   4 → +1.5   5 → +2.5

    A positive weight pulls toward a book's emotional direction ("want more of
    this"); a negative weight subtracts it, pushing toward the opposite direction
    in the centered space ("want the opposite"). The result is normalized.

    (No complement / non-negative clamp: those were artifacts of the old [0,1]
    vectors. In mean-centered space the opposite of a profile is simply its
    negation, which the signed weight already produces.)
    """
    preference = np.zeros_like(vectors[0])

    for vec, rating in zip(vectors, ratings):
        preference += vec * (rating - RATING_MIDPOINT)

    norm = np.linalg.norm(preference)
    if norm > 0:
        preference = preference / norm

    return preference


@router.post("/recommend", response_model=list[MediaSimilarResponse])
async def recommend_media(
    req: RecommendRequest,
    db: AsyncSession = Depends(get_db),
):
    if not req.ratings:
        raise HTTPException(status_code=400, detail="At least one rating is required")

    vectors = []
    ratings = []
    rated_ids = set()

    for r in req.ratings:
        item = await db.get(MediaItem, r.media_id)
        if not item:
            raise HTTPException(
                status_code=404, detail=f"Media item {r.media_id} not found"
            )
        if item.emotion_vector is None:
            raise HTTPException(
                status_code=400,
                detail=f"'{item.title}' has not been analyzed yet",
            )
        vectors.append(np.array(item.emotion_vector, dtype=np.float64))
        ratings.append(r.rating)
        rated_ids.add(str(item.id))

    preference = build_preference_vector(vectors, ratings)

    vector_str = "[" + ",".join(str(v) for v in preference.tolist()) + "]"

    placeholders = ", ".join(f"'{rid}'" for rid in rated_ids)
    query = text(
        f"""
        SELECT id, 1 - (emotion_vector <=> CAST(:vec AS vector)) as similarity
        FROM media
        WHERE id NOT IN ({placeholders}) AND emotion_vector IS NOT NULL
        ORDER BY emotion_vector <=> CAST(:vec AS vector)
        LIMIT :lim
        """
    )
    result = await db.execute(query, {"vec": vector_str, "lim": req.limit})
    rows = result.fetchall()

    recommendations = []
    for row in rows:
        item = await db.get(MediaItem, row[0])
        recommendations.append(
            MediaSimilarResponse(
                item=MediaResponse.from_orm_item(item),
                similarity=round(float(row[1]), 4),
            )
        )
    return recommendations
