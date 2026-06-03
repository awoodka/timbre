"""Shared fixtures for the embedding test suite.

Loads the seeded corpus (stored, standardized vectors) once per session straight
from the DB, so individual tests are plain synchronous functions operating on
numpy vectors. DB SSL follows the app's env-driven setting (DB_SSL).

Two views:
- `corpus`       — BOOKS only, keyed by title (the original single-medium suite).
- `media_corpus` — ALL media, keyed by (medium, title) (cross-media tests; books
                   and their film adaptations share a title, hence the tuple key).
"""

import asyncio

import numpy as np
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.media import MediaItem


async def _load_all() -> list:
    engine = create_async_engine(
        settings.database_url, connect_args={"ssl": settings.db_ssl}
    )
    try:
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as s:
            rows = (
                await s.execute(select(MediaItem).where(MediaItem.emotion_vector.isnot(None)))
            ).scalars().all()
            return [
                {
                    "medium": m.medium,
                    "title": m.title,
                    "vec": np.array(list(m.emotion_vector), dtype=np.float64),
                    "scores": dict(m.emotion_breakdown),
                }
                for m in rows
            ]
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def _all_media() -> list:
    data = asyncio.run(_load_all())
    assert len(data) >= 40, (
        f"Expected the seeded corpus; got {len(data)} analyzed items. Is the DB seeded?"
    )
    return data


@pytest.fixture(scope="session")
def corpus(_all_media) -> dict:
    """Books only, keyed by title — the original single-medium test surface."""
    return {
        m["title"]: {"vec": m["vec"], "scores": m["scores"]}
        for m in _all_media
        if m["medium"] == "book"
    }


@pytest.fixture(scope="session")
def media_corpus(_all_media) -> dict:
    """All media, keyed by (medium, title) — for cross-media tests."""
    return {
        (m["medium"], m["title"]): {"vec": m["vec"], "scores": m["scores"]}
        for m in _all_media
    }
