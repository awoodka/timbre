"""Backfill cover images for any media items still missing one.

Cover-only and idempotent: for each item with an empty cover_image_url, re-fetch
ONLY the per-medium metadata (TMDB / RAWG / Google Books — no Gemini, no scraping)
via the same `lookup_metadata` the analysis uses, and store any cover it returns.
Books fall back to Open Library when Google Books comes up empty (it's keyless and
rate-limits aggressively).

Run after seeding a new batch — items arrive cover-less whenever a metadata key was
missing or an external API was throttled. Safe to re-run: only touches items that
still lack a cover.

Usage:  docker compose exec backend python -m backfill_covers
"""

import asyncio
import logging

import httpx
from sqlalchemy import or_, select

from app.database import async_session, init_db
from app.models.media import MediaItem
from app.services.sources import lookup_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _openlibrary_cover(client: httpx.AsyncClient, title: str, creator: str) -> str:
    """Fallback book cover via Open Library (keyless). Try title+author, then title-only
    (translated classics and multi-author works often miss on the author match)."""
    for params in (
        {"title": title, "author": creator, "limit": 1, "fields": "cover_i"},
        {"title": title, "limit": 1, "fields": "cover_i"},
    ):
        try:
            resp = await client.get("https://openlibrary.org/search.json", params=params)
            resp.raise_for_status()
            docs = resp.json().get("docs", [])
            cover_id = docs[0].get("cover_i") if docs else None
            if cover_id:
                return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
        except Exception:
            continue
    return ""


async def main():
    await init_db()
    async with async_session() as session:
        items = (await session.execute(
            select(MediaItem)
            .where(or_(MediaItem.cover_image_url.is_(None), MediaItem.cover_image_url == ""))
            .order_by(MediaItem.medium, MediaItem.title)
        )).scalars().all()
        logger.info(f"{len(items)} items missing a cover")

        filled = 0
        async with httpx.AsyncClient(timeout=10) as client:
            for item in items:
                url = ""
                try:
                    meta = await lookup_metadata(item.medium, item.title, item.creator)
                    url = (meta or {}).get("cover_image_url") or ""
                except Exception as e:
                    logger.warning(f"  lookup failed: [{item.medium}] {item.title} -- {e}")
                # Books: fall back to Open Library when Google Books returns nothing.
                if not url and item.medium == "book":
                    url = await _openlibrary_cover(client, item.title, item.creator)

                if url:
                    item.cover_image_url = url
                    filled += 1
                    logger.info(f"  cover:  [{item.medium}] {item.title}")
                else:
                    logger.info(f"  NONE:   [{item.medium}] {item.title}")
                await session.commit()
                await asyncio.sleep(0.4)  # stay under external rate limits

        logger.info(f"Done. Filled {filled}/{len(items)} missing covers.")


if __name__ == "__main__":
    asyncio.run(main())
