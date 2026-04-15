import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.book import Book
from app.schemas import BookResponse, BookSimilarResponse, RecommendRequest

router = APIRouter(prefix="/api", tags=["recommendations"])

# Rating midpoint: ratings above this pull toward, below push away
RATING_MIDPOINT = 2.5


def build_preference_vector(
    vectors: list[np.ndarray], ratings: list[float]
) -> np.ndarray:
    """
    Build an emotional preference vector from rated books.

    Midpoint is 2.5 on the 1-5 scale:
      1 → -1.5 (strong negative)
      2 → -0.5 (mild negative)
      3 → +0.5 (mild positive)
      4 → +1.5 (positive)
      5 → +2.5 (strong positive)

    Positive ratings add the book's emotion vector (want MORE of these emotions).
    Negative ratings add the COMPLEMENT (1 - vector), meaning "I want the opposite
    of this emotional profile." This way a 1-star rating on a high-dread book
    actively pushes toward low-dread, high-warmth books rather than collapsing
    to zero.

    The result is clamped to non-negative and normalized to a unit vector.
    """
    preference = np.zeros_like(vectors[0])

    for vec, rating in zip(vectors, ratings):
        weight = rating - RATING_MIDPOINT
        if weight >= 0:
            # Positive: want more of these emotions
            preference += vec * weight
        else:
            # Negative: want the opposite emotional profile
            complement = 1.0 - vec
            preference += complement * abs(weight)

    # Clamp to non-negative
    preference = np.clip(preference, 0, None)

    # Normalize to unit vector
    norm = np.linalg.norm(preference)
    if norm > 0:
        preference = preference / norm

    return preference


@router.post("/recommend", response_model=list[BookSimilarResponse])
async def recommend_books(
    req: RecommendRequest,
    db: AsyncSession = Depends(get_db),
):
    if not req.ratings:
        raise HTTPException(status_code=400, detail="At least one rating is required")

    vectors = []
    ratings = []
    rated_ids = set()

    for r in req.ratings:
        book = await db.get(Book, r.book_id)
        if not book:
            raise HTTPException(
                status_code=404, detail=f"Book {r.book_id} not found"
            )
        if book.emotion_vector is None:
            raise HTTPException(
                status_code=400,
                detail=f"Book '{book.title}' has not been analyzed yet",
            )
        vectors.append(np.array(book.emotion_vector, dtype=np.float64))
        ratings.append(r.rating)
        rated_ids.add(str(book.id))

    preference = build_preference_vector(vectors, ratings)

    vector_str = "[" + ",".join(str(v) for v in preference.tolist()) + "]"

    placeholders = ", ".join(f"'{rid}'" for rid in rated_ids)
    query = text(
        f"""
        SELECT id, 1 - (emotion_vector <=> CAST(:vec AS vector)) as similarity
        FROM books
        WHERE id NOT IN ({placeholders}) AND emotion_vector IS NOT NULL
        ORDER BY emotion_vector <=> CAST(:vec AS vector)
        LIMIT :lim
        """
    )
    result = await db.execute(query, {"vec": vector_str, "lim": req.limit})
    rows = result.fetchall()

    recommendations = []
    for row in rows:
        book = await db.get(Book, row[0])
        recommendations.append(
            BookSimilarResponse(
                book=BookResponse.from_orm_book(book),
                similarity=round(float(row[1]), 4),
            )
        )
    return recommendations
