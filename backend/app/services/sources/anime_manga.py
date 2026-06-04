"""Anime & manga metadata source: Jikan (MyAnimeList API v4 — free, no key).

One module, two fetchers (anime / manga). Mirrors book.py's return shape. Titles
are stored as `title_english` when available so the manga and anime of the same
work share a title (enabling manga↔anime cross-media pairs).
"""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

JIKAN = "https://api.jikan.moe/v4"


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _pick(results: list, title: str, prefer_types: set):
    """Choose the best match: exact-title, then preferred type, then top score."""
    if not results:
        return None
    t = _norm(title)
    exact = [r for r in results if _norm(r.get("title_english")) == t or _norm(r.get("title")) == t]
    pool = exact or results
    typed = [r for r in pool if r.get("type") in prefer_types]
    pool = typed or pool
    return max(pool, key=lambda r: r.get("score") or -1)


async def _search(client: httpx.AsyncClient, kind: str, title: str) -> list:
    params = {"q": title, "limit": 8}
    r = await client.get(f"{JIKAN}/{kind}", params=params)
    if r.status_code == 429:  # rate limited — brief backoff, one retry
        await asyncio.sleep(1.5)
        r = await client.get(f"{JIKAN}/{kind}", params=params)
    r.raise_for_status()
    return r.json().get("data", [])


def _to_metadata(r: dict, creators: list) -> dict:
    img = (r.get("images") or {}).get("jpg", {}).get("large_image_url") or ""
    date = (r.get("aired") or r.get("published") or {}).get("prop", {}).get("from", {}).get("year")
    return {
        "title": r.get("title_english") or r.get("title", ""),
        "creators": creators,
        "description": r.get("synopsis") or "",
        "categories": [g["name"] for g in r.get("genres", [])],
        "average_rating": r.get("score"),
        "published_date": str(date or ""),
        "cover_image_url": img,
    }


async def fetch_anime(title: str, creator: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            results = await _search(client, "anime", title)
            r = _pick(results, title, {"TV", "ONA"})
            if not r:
                logger.info(f"Jikan: no anime for '{title}'")
                return {}
            return _to_metadata(r, [s["name"] for s in r.get("studios", [])])
    except Exception as e:
        logger.warning(f"Jikan anime error for '{title}': {e}")
        return {}


async def fetch_manga(title: str, creator: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            results = await _search(client, "manga", title)
            r = _pick(results, title, {"Manga"})
            if not r:
                logger.info(f"Jikan: no manga for '{title}'")
                return {}
            return _to_metadata(r, [a["name"] for a in r.get("authors", [])])
    except Exception as e:
        logger.warning(f"Jikan manga error for '{title}': {e}")
        return {}
