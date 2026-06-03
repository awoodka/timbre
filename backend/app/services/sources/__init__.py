"""Per-medium context gathering.

Each medium contributes a `fetch_metadata(title, creator) -> dict` (the analog of
Google Books for films/games/etc.); the web-essay and Reddit discourse scraping
is shared and only adapts its search wording per medium. To add a medium: write a
`fetch_metadata` and register it in `_METADATA_FETCHERS`.

`gather_context` returns a uniform shape consumed by emotional_analysis:
    {"metadata": {...}, "essays": [...], "reddit": [...]}
"""

import asyncio

from app.services.sources import book as _book
from app.services.sources import film as _film
from app.services.sources import web as _web

# Human-readable noun per medium, used in prompts and search queries.
MEDIUM_NOUNS = {
    "book": "book",
    "film": "film",
    "show": "TV show",
    "game": "video game",
    "manga": "manga",
    "anime": "anime series",
    "music": "album",
}

# medium -> async (title, creator) -> metadata dict
_METADATA_FETCHERS = {
    "book": _book.fetch_metadata,
    "film": _film.fetch_metadata,
}


async def _fetch_metadata(medium: str, title: str, creator: str) -> dict:
    fetch = _METADATA_FETCHERS.get(medium)
    return await fetch(title, creator) if fetch else {}


async def gather_context(medium: str, title: str, creator: str) -> dict:
    """Gather metadata + discourse for any medium."""
    noun = MEDIUM_NOUNS.get(medium, medium)
    metadata, essays, reddit = await asyncio.gather(
        _fetch_metadata(medium, title, creator),
        _web.search_and_scrape_essays(title, creator, noun),
        _web.search_reddit(title, creator, noun),
    )
    return {"metadata": metadata, "essays": essays, "reddit": reddit}
