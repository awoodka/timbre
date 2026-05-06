"""Backfill cover images from Open Library for all books missing covers."""

import asyncio
import logging

import httpx
from sqlalchemy import select
from app.database import init_db, async_session
from app.models.book import Book

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_cover(client: httpx.AsyncClient, title: str, author: str) -> str:
    """Search Open Library for a book and return a cover image URL."""
    try:
        resp = await client.get(
            "https://openlibrary.org/search.json",
            params={"title": title, "author": author, "limit": 1, "fields": "cover_i,title,author_name"},
        )
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("docs", [])
        if not docs:
            return ""
        cover_id = docs[0].get("cover_i")
        if not cover_id:
            return ""
        # Open Library cover API — M = medium (~180px, sufficient for UI)
        return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
    except Exception as e:
        logger.warning(f"Failed for '{title}': {e}")
        return ""


async def main():
    await init_db()
    async with async_session() as s:
        books = (await s.execute(
            select(Book).where(Book.cover_image_url.is_(None) | (Book.cover_image_url == ""))
        )).scalars().all()
        logger.info(f"Found {len(books)} books without covers")

        async with httpx.AsyncClient(timeout=10) as client:
            for book in books:
                url = await fetch_cover(client, book.title, book.author)
                if url:
                    book.cover_image_url = url
                    logger.info(f"  Cover: {book.title}")
                else:
                    logger.warning(f"  No cover: {book.title}")
                await asyncio.sleep(0.3)

        await s.commit()
    logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
