"""Shared fixtures for the embedding test suite.

Loads the seeded corpus (stored, standardized vectors) once per session straight
from the DB, so individual tests are plain synchronous functions operating on
numpy vectors. DB SSL follows the app's env-driven setting (DB_SSL).
"""

import asyncio

import numpy as np
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.book import Book


async def _load_corpus() -> dict:
    engine = create_async_engine(
        settings.database_url, connect_args={"ssl": settings.db_ssl}
    )
    try:
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as s:
            rows = (
                await s.execute(select(Book).where(Book.emotion_vector.isnot(None)))
            ).scalars().all()
            return {
                b.title: {
                    "vec": np.array(list(b.emotion_vector), dtype=np.float64),
                    "scores": dict(b.emotion_breakdown),
                }
                for b in rows
            }
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def corpus() -> dict:
    """All analyzed books: {title: {"vec": np.ndarray, "scores": dict}}."""
    data = asyncio.run(_load_corpus())
    assert len(data) >= 40, (
        f"Expected the full seeded corpus (~50 analyzed books); got {len(data)}. "
        "Is the DB seeded and re-scored?"
    )
    return data
