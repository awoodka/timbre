"""
Re-score all books using existing emotional profiles but updated dimensions.
Only runs Step 2 (scoring) and Step 3 (normalization) — no web scraping or profile generation.
"""

import asyncio
import json
import logging

from sqlalchemy import select
from app.database import init_db, async_session
from app.models.book import Book
from app.services.emotional_analysis import score_emotional_dimensions, normalize_vector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    await init_db()

    async with async_session() as s:
        books = (await s.execute(
            select(Book).where(Book.description.isnot(None))
        )).scalars().all()
        logger.info(f"Re-scoring {len(books)} books with updated dimensions...")

        for book in books:
            logger.info(f"Scoring: {book.title}...")
            try:
                scores = await score_emotional_dimensions(
                    book.title, book.author, book.description
                )
                vector = normalize_vector(scores)
                book.emotion_breakdown = scores
                book.emotion_vector = vector
                book.analysis_status = "completed"

                # Update raw response with new scores
                if book.raw_claude_response:
                    try:
                        raw = json.loads(book.raw_claude_response)
                        raw["scores"] = scores
                        book.raw_claude_response = json.dumps(raw, indent=2)
                    except json.JSONDecodeError:
                        pass

                await s.commit()
                logger.info(f"  Done: {book.title}")
            except Exception as e:
                logger.error(f"  Failed: {book.title} -- {e}")
                book.analysis_status = "failed"
                await s.commit()

    logger.info("Re-scoring complete.")


if __name__ == "__main__":
    asyncio.run(main())
