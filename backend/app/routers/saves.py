from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.media import MediaItem
from app.models.user import SavedItem, User
from app.schemas import SavedItemResponse

router = APIRouter(prefix="/api/saves", tags=["saves"])


@router.get("", response_model=list[SavedItemResponse])
async def list_saves(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = await db.scalars(
        select(SavedItem)
        .where(SavedItem.user_id == user.id)
        .order_by(SavedItem.created_at.desc())
    )
    return list(rows)


@router.post("/{media_id}", response_model=SavedItemResponse)
async def add_save(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await db.get(MediaItem, media_id):
        raise HTTPException(status_code=404, detail="Media not found")
    existing = await db.scalar(
        select(SavedItem).where(SavedItem.user_id == user.id, SavedItem.media_id == media_id)
    )
    if not existing:  # idempotent — saving an already-saved work is a no-op
        existing = SavedItem(user_id=user.id, media_id=media_id)
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
    return existing


@router.delete("/{media_id}")
async def remove_save(
    media_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.scalar(
        select(SavedItem).where(SavedItem.user_id == user.id, SavedItem.media_id == media_id)
    )
    if existing:
        await db.delete(existing)
        await db.commit()
    return {"ok": True}
