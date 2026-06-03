"""One-time migration: generalize the `books` table into `media`.

Renames books->media, author->creator, isbn->external_id,
raw_claude_response->raw_response, and adds a `medium` column (default 'book').
Idempotent and non-destructive: preserves all rows and their emotion vectors.

Usage:  python -m migrate_to_media
"""

import asyncio
import logging

from sqlalchemy import text

from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RENAME_TABLE = "ALTER TABLE IF EXISTS books RENAME TO media"

COLUMNS = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='media' AND column_name='author') THEN
        ALTER TABLE media RENAME COLUMN author TO creator;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='media' AND column_name='isbn') THEN
        ALTER TABLE media RENAME COLUMN isbn TO external_id;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='media' AND column_name='raw_claude_response') THEN
        ALTER TABLE media RENAME COLUMN raw_claude_response TO raw_response;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='media' AND column_name='medium') THEN
        ALTER TABLE media ADD COLUMN medium VARCHAR(20) NOT NULL DEFAULT 'book';
    END IF;
END $$;
"""


async def _count(name: str):
    async with engine.connect() as conn:
        try:
            return (await conn.execute(text(f"SELECT count(*) FROM {name}"))).scalar()
        except Exception:
            return None


async def main():
    before = await _count("books")
    async with engine.begin() as conn:
        await conn.execute(text(RENAME_TABLE))
        await conn.execute(text(COLUMNS))
    after = await _count("media")
    logger.info(f"Migration complete. rows: books(before)={before} -> media(after)={after}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
