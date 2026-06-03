"""
Re-score all books with the updated pipeline (v2).

This runs profile regeneration + scoring + normalization, WITHOUT re-scraping
external context: each book's existing stored profile is fed back in as source
material and re-distilled through the updated "dominant signature + arc" prompt,
then re-scored on the current dimension set.

Use this after changing the prompts or the dimension list. It:
  1. Backs up current scores/vectors/profiles to a timestamped JSON.
  2. Migrates the emotion_vector column to the current NUM_DIMENSIONS width.
  3. Regenerates the profile and re-scores every book.

Usage:  python -m rescore
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, text
from app.database import init_db, async_session, engine
from app.dimensions import NUM_DIMENSIONS
from app.models.media import MediaItem
from app.services.emotional_analysis import (
    generate_emotional_profile,
    score_emotional_dimensions,
    normalize_vector,
)
from app.services.embeddings import recompute_all_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Small delay between books to stay under Gemini rate limits.
PER_BOOK_DELAY_SECONDS = 1.5


async def backup_current(session) -> Path:
    items = (await session.execute(select(MediaItem))).scalars().all()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path(__file__).parent / f"rescore_backup_{stamp}.json"
    payload = [
        {
            "id": str(b.id),
            "title": b.title,
            "creator": b.creator,
            "description": b.description,
            "emotion_breakdown": b.emotion_breakdown,
            "emotion_vector": [float(x) for x in b.emotion_vector] if b.emotion_vector is not None else None,
        }
        for b in items
    ]
    path.write_text(json.dumps(payload, indent=2))
    logger.info(f"Backed up {len(payload)} items -> {path.name}")
    return path


async def migrate_vector_width():
    """Drop & re-add emotion_vector at the current dimension width.

    Safe because we re-populate every vector in this run. pgvector cannot cast
    between widths, so a clean re-add is simplest.
    """
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE media DROP COLUMN IF EXISTS emotion_vector"))
        await conn.execute(
            text(f"ALTER TABLE media ADD COLUMN emotion_vector vector({NUM_DIMENSIONS})")
        )
    logger.info(f"emotion_vector column migrated to vector({NUM_DIMENSIONS})")


async def main():
    await init_db()

    async with async_session() as session:
        await backup_current(session)

    await migrate_vector_width()

    async with async_session() as session:
        items = (
            await session.execute(select(MediaItem).where(MediaItem.description.isnot(None)))
        ).scalars().all()
        logger.info(f"Re-scoring {len(items)} items (NUM_DIMENSIONS={NUM_DIMENSIONS})...")

        ok, failed = 0, 0
        for item in items:
            logger.info(f"[{ok + failed + 1}/{len(items)}] {item.title}")
            try:
                # Re-distill the existing profile through the updated prompt
                # (existing profile fed in as source material — no re-scraping).
                context = {
                    "metadata": {},
                    "essays": [
                        {
                            "source_title": "Prior synthesized emotional profile",
                            "source_url": "",
                            "content": item.description,
                        }
                    ],
                    "reddit": [],
                }
                profile = await generate_emotional_profile(
                    item.medium, item.title, item.creator, context
                )
                scores = await score_emotional_dimensions(
                    item.medium, item.title, item.creator, profile
                )
                vector = normalize_vector(scores)

                item.description = profile
                item.emotion_breakdown = scores
                item.emotion_vector = vector
                item.analysis_status = "completed"

                if item.raw_response:
                    try:
                        raw = json.loads(item.raw_response)
                        raw["profile"] = profile
                        raw["scores"] = scores
                        item.raw_response = json.dumps(raw, indent=2)
                    except json.JSONDecodeError:
                        pass

                await session.commit()
                ok += 1
            except Exception as e:
                logger.error(f"  Failed: {item.title} -- {e}")
                item.analysis_status = "failed"
                await session.commit()
                failed += 1

            await asyncio.sleep(PER_BOOK_DELAY_SECONDS)

    # Standardize all vectors against the corpus centroid (mean-centering).
    async with async_session() as session:
        n = await recompute_all_embeddings(session)
        logger.info(f"Standardized {n} embeddings against corpus centroid")

    logger.info(f"Re-scoring complete. {ok} succeeded, {failed} failed.")


if __name__ == "__main__":
    asyncio.run(main())
