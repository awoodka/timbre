import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.media import MediaItem
from app.models.user import User
from app.schemas import (
    MediaCreate,
    MediaLookupRequest,
    MediaLookupResponse,
    MediaResponse,
    MediaSimilarResponse,
)
from app.services.emotional_analysis import analyze_media
from app.services.sources import lookup_metadata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/media", tags=["media"])


async def _run_analysis(media_id: uuid.UUID, medium: str, title: str, creator: str):
    """Background task: run emotional analysis, then re-standardize the corpus."""
    from app.database import async_session
    from app.services.embeddings import recompute_all_embeddings

    try:
        result = await analyze_media(medium, title, creator)
        async with async_session() as session:
            item = await session.get(MediaItem, media_id)
            if item:
                item.description = result["description"]
                item.emotion_breakdown = result["emotion_breakdown"]
                item.emotion_vector = result["emotion_vector"]
                item.raw_response = result["raw_response"]
                if result.get("cover_image_url"):
                    item.cover_image_url = result["cover_image_url"]
                item.analysis_status = "completed"
                await session.commit()
                # Keep every stored vector in one consistent mean-centered space.
                await recompute_all_embeddings(session)
    except Exception as e:
        logger.error(f"Analysis failed for {title}: {e}")
        async with async_session() as session:
            item = await session.get(MediaItem, media_id)
            if item:
                item.analysis_status = "failed"
                item.raw_response = str(e)
                await session.commit()


@router.post("", response_model=MediaResponse, status_code=201)
async def create_media(
    item_in: MediaCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = MediaItem(
        medium=item_in.medium,
        title=item_in.title,
        creator=item_in.creator,
        external_id=item_in.external_id,
        cover_image_url=item_in.cover_image_url,
        metadata_=item_in.metadata,
        analysis_status="pending",
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    background_tasks.add_task(
        _run_analysis, item.id, item.medium, item.title, item.creator
    )
    return MediaResponse.from_orm_item(item)


@router.post("/lookup", response_model=MediaLookupResponse)
async def lookup_media(
    req: MediaLookupRequest,
    user: User = Depends(get_current_user),
):
    """Single-best-match metadata lookup for the add-media confirm step.

    Hits the medium's external API (Google Books / TMDB / RAWG / Jikan) via the
    same fetcher analysis uses. Returns found=false on no match or a missing API
    key — the UI then offers an 'add as typed' path.
    """
    meta = await lookup_metadata(req.medium, req.title, req.creator)
    if not meta:
        return MediaLookupResponse(found=False)
    creators = meta.get("creators") or []
    return MediaLookupResponse(
        found=True,
        title=meta.get("title") or req.title,
        creator=(creators[0] if creators else req.creator) or "",
        year=(meta.get("published_date") or "")[:4],
        cover_image_url=meta.get("cover_image_url") or "",
        description=meta.get("description") or "",
    )


@router.get("", response_model=list[MediaResponse])
async def list_media(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MediaItem).order_by(MediaItem.created_at.desc()))
    return [MediaResponse.from_orm_item(m) for m in result.scalars().all()]


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(media_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    item = await db.get(MediaItem, media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media item not found")
    return MediaResponse.from_orm_item(item)


@router.get("/{media_id}/similar", response_model=list[MediaSimilarResponse])
async def get_similar(
    media_id: uuid.UUID,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(MediaItem, media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media item not found")
    if item.emotion_vector is None:
        raise HTTPException(status_code=400, detail="Item has not been analyzed yet")

    vector_str = "[" + ",".join(str(v) for v in item.emotion_vector) + "]"
    query = text(
        """
        SELECT id, 1 - (emotion_vector <=> CAST(:vec AS vector)) as similarity
        FROM media
        WHERE id != :item_id AND emotion_vector IS NOT NULL
        ORDER BY emotion_vector <=> CAST(:vec AS vector)
        LIMIT :lim
        """
    )
    result = await db.execute(
        query, {"vec": vector_str, "item_id": str(media_id), "lim": limit}
    )
    similar = []
    for row in result.fetchall():
        sim_item = await db.get(MediaItem, row[0])
        similar.append(
            MediaSimilarResponse(
                item=MediaResponse.from_orm_item(sim_item),
                similarity=round(float(row[1]), 4),
            )
        )
    return similar


@router.post("/{media_id}/reanalyze", response_model=MediaResponse)
async def reanalyze_media(
    media_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await db.get(MediaItem, media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media item not found")

    item.analysis_status = "pending"
    await db.commit()

    background_tasks.add_task(
        _run_analysis, item.id, item.medium, item.title, item.creator
    )
    await db.refresh(item)
    return MediaResponse.from_orm_item(item)
