"""Rebuild all standardized emotion vectors from stored scores.

Pure arithmetic on emotion_breakdown — no LLM calls. Use this after changing the
standardization logic, or to re-standardize the corpus on demand.

Usage:  python -m rebuild_embeddings
"""

import asyncio
import logging

from app.database import async_session
from app.services.embeddings import recompute_all_embeddings

logging.basicConfig(level=logging.INFO)


async def main():
    async with async_session() as session:
        n = await recompute_all_embeddings(session)
        print(f"Re-standardized {n} embeddings against the corpus centroid.")


if __name__ == "__main__":
    asyncio.run(main())
