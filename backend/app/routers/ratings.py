from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.media import MediaItem
from app.models.user import Rating, User
from app.schemas import RatingResponse, RatingUpsert

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.get("", response_model=list[RatingResponse])
async def list_ratings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = await db.scalars(select(Rating).where(Rating.user_id == user.id))
    return list(rows)


@router.put("/{media_id}", response_model=RatingResponse)
async def upsert_rating(
    media_id: UUID,
    data: RatingUpsert,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await db.get(MediaItem, media_id):
        raise HTTPException(status_code=404, detail="Media not found")
    existing = await db.scalar(
        select(Rating).where(Rating.user_id == user.id, Rating.media_id == media_id)
    )
    if existing:
        existing.rating = data.rating
    else:
        existing = Rating(user_id=user.id, media_id=media_id, rating=data.rating)
        db.add(existing)
    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{media_id}")
async def delete_rating(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.scalar(
        select(Rating).where(Rating.user_id == user.id, Rating.media_id == media_id)
    )
    if existing:
        await db.delete(existing)
        await db.commit()
    return {"ok": True}
