"""One-off migration: add the nullable `enjoyment` (1–5 star) column to `ratings`.

The project has no Alembic, and `create_all` won't alter an existing table — so this
adds the column with a raw, idempotent `ALTER TABLE` (safe to re-run). Run once:

    python migrate_add_enjoyment.py
"""

import asyncio
import logging

from sqlalchemy import text

from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE ratings ADD COLUMN IF NOT EXISTS enjoyment INTEGER "
                "CHECK (enjoyment BETWEEN 1 AND 5)"
            )
        )
    logger.info("ratings.enjoyment column ensured")


if __name__ == "__main__":
    asyncio.run(main())
