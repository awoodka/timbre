"""Video-game metadata source: RAWG API (requires a free RAWG_API_KEY).

Mirrors film.py's contract. RAWG search results omit description/developers, so
the chosen game gets one details call. Disambiguates by exact-name then rating
(remakes resolve to the highest-rated entry).
"""

import logging

import httpx

from app.config import settings

RAWG = "https://api.rawg.io/api"
logger = logging.getLogger(__name__)


def _norm(s: str) -> str:
    return (s or "").strip().lower()


async def fetch_metadata(title: str, creator: str) -> dict:
    key = settings.rawg_api_key
    if not key:
        logger.warning("RAWG_API_KEY not set; skipping game metadata for '%s'", title)
        return {}

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(
                f"{RAWG}/games", params={"key": key, "search": title, "page_size": 8}
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                logger.info(f"RAWG: no results for '{title}'")
                return {}

            t = _norm(title)
            exact = [g for g in results if _norm(g.get("name")) == t]
            pool = exact or results
            chosen = max(pool, key=lambda g: g.get("rating") or 0)

            d = (await client.get(
                f"{RAWG}/games/{chosen['id']}", params={"key": key}
            )).json()
            return {
                "title": d.get("name") or chosen.get("name", ""),
                "creators": [x["name"] for x in d.get("developers", [])],
                "description": d.get("description_raw") or "",
                "categories": [g["name"] for g in d.get("genres", [])],
                "average_rating": d.get("rating"),
                "published_date": (d.get("released") or "")[:4],
                "cover_image_url": d.get("background_image") or chosen.get("background_image") or "",
            }
        except Exception as e:
            logger.warning(f"RAWG API error for '{title}': {e}")
            return {}
