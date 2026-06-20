"""One-time migration: rebuild the `ratings` table for per-emotion feedback.

The old table stored a single 1-5 star (`rating`). The new schema stores per-emotion
`feedback` (JSON {emotion_key: -1|1}) plus a derived `resonance` (float). A star can't
be converted to per-emotion marks, so the old rows are dropped (MVP data only).

Usage:  python -m migrate_ratings_feedback   (from backend/, with the venv active)
A fresh database needs no migration — `create_all` builds the new schema directly.
"""

import asyncio
import logging

from sqlalchemy import text

from app.database import engine, init_db
import app.models.media  # noqa: F401  -- register MediaItem with Base.metadata
import app.models.user  # noqa: F401  -- register User/Rating with Base.metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS ratings CASCADE"))
    logger.info("Dropped old ratings table")
    await init_db()  # create_all rebuilds `ratings` with feedback (JSON) + resonance (float)
    logger.info("Rebuilt ratings table for per-emotion feedback")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
