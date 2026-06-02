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
from app.models.book import Book
from app.services.emotional_analysis import (
    generate_emotional_profile,
    score_emotional_dimensions,
    normalize_vector,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Small delay between books to stay under Gemini rate limits.
PER_BOOK_DELAY_SECONDS = 1.5


async def backup_current(session) -> Path:
    books = (await session.execute(select(Book))).scalars().all()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path(__file__).parent / f"rescore_backup_{stamp}.json"
    payload = [
        {
            "id": str(b.id),
            "title": b.title,
            "author": b.author,
            "description": b.description,
            "emotion_breakdown": b.emotion_breakdown,
            "emotion_vector": [float(x) for x in b.emotion_vector] if b.emotion_vector is not None else None,
        }
        for b in books
    ]
    path.write_text(json.dumps(payload, indent=2))
    logger.info(f"Backed up {len(payload)} books -> {path.name}")
    return path


async def migrate_vector_width():
    """Drop & re-add emotion_vector at the current dimension width.

    Safe because we re-populate every vector in this run. pgvector cannot cast
    between widths, so a clean re-add is simplest.
    """
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE books DROP COLUMN IF EXISTS emotion_vector"))
        await conn.execute(
            text(f"ALTER TABLE books ADD COLUMN emotion_vector vector({NUM_DIMENSIONS})")
        )
    logger.info(f"emotion_vector column migrated to vector({NUM_DIMENSIONS})")


async def main():
    await init_db()

    async with async_session() as session:
        await backup_current(session)

    await migrate_vector_width()

    async with async_session() as session:
        books = (
            await session.execute(select(Book).where(Book.description.isnot(None)))
        ).scalars().all()
        logger.info(f"Re-scoring {len(books)} books (NUM_DIMENSIONS={NUM_DIMENSIONS})...")

        ok, failed = 0, 0
        for book in books:
            logger.info(f"[{ok + failed + 1}/{len(books)}] {book.title}")
            try:
                # Re-distill the existing profile through the updated prompt
                # (existing profile fed in as source material — no re-scraping).
                context = {
                    "google_books": {},
                    "essays": [
                        {
                            "source_title": "Prior synthesized emotional profile",
                            "source_url": "",
                            "content": book.description,
                        }
                    ],
                    "reddit": [],
                }
                profile = await generate_emotional_profile(book.title, book.author, context)
                scores = await score_emotional_dimensions(book.title, book.author, profile)
                vector = normalize_vector(scores)

                book.description = profile
                book.emotion_breakdown = scores
                book.emotion_vector = vector
                book.analysis_status = "completed"

                if book.raw_claude_response:
                    try:
                        raw = json.loads(book.raw_claude_response)
                        raw["profile"] = profile
                        raw["scores"] = scores
                        book.raw_claude_response = json.dumps(raw, indent=2)
                    except json.JSONDecodeError:
                        pass

                await session.commit()
                ok += 1
            except Exception as e:
                logger.error(f"  Failed: {book.title} -- {e}")
                book.analysis_status = "failed"
                await session.commit()
                failed += 1

            await asyncio.sleep(PER_BOOK_DELAY_SECONDS)

    logger.info(f"Re-scoring complete. {ok} succeeded, {failed} failed.")


if __name__ == "__main__":
    asyncio.run(main())
