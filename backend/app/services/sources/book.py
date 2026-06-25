"""Book metadata source: Google Books API (free, no key required)."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


async def fetch_metadata(title: str, creator: str) -> dict:
    """Return a uniform metadata dict for a book via the Google Books API."""
    query = f"{title} {creator}".strip()
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": query, "maxResults": 1}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:  # anonymous quota — brief backoff, one retry
                await asyncio.sleep(1.5)
                resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("items"):
                logger.info(f"Google Books: no results for '{query}'")
                return {}

            info = data["items"][0]["volumeInfo"]
            image_links = info.get("imageLinks", {})
            cover_url = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
            if cover_url.startswith("http://"):
                cover_url = "https://" + cover_url[7:]

            return {
                "title": info.get("title", ""),
                "creators": info.get("authors", []),
                "description": info.get("description", ""),
                "categories": info.get("categories", []),
                "average_rating": info.get("averageRating"),
                "published_date": info.get("publishedDate", ""),
                "cover_image_url": cover_url,
            }
        except Exception as e:
            logger.warning(f"Google Books API error: {e}")
            return {}
