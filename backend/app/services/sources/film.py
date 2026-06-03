"""Film metadata source: TMDB API (requires a free TMDB_API_KEY).

Mirrors book.py's fetch_metadata contract. Disambiguates remakes (e.g. Solaris
1972 vs 2002) by matching the director against the stored `creator`, since the
most-popular result is often the wrong version.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TMDB = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"


async def _director(client: httpx.AsyncClient, movie_id: int, key: str) -> str:
    try:
        r = await client.get(f"{TMDB}/movie/{movie_id}/credits", params={"api_key": key})
        r.raise_for_status()
        for c in r.json().get("crew", []):
            if c.get("job") == "Director":
                return c.get("name", "")
    except Exception:
        pass
    return ""


def _director_matches(director: str, creator: str) -> bool:
    if not director or not creator:
        return False
    d, c = director.lower(), creator.lower()
    return d == c or c.split()[-1] in d  # exact or shared last-name token


async def fetch_metadata(title: str, creator: str) -> dict:
    """Return a uniform metadata dict for a film via TMDB."""
    key = settings.tmdb_api_key
    if not key:
        logger.warning("TMDB_API_KEY not set; skipping film metadata for '%s'", title)
        return {}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{TMDB}/search/movie", params={"api_key": key, "query": title}
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                logger.info(f"TMDB: no results for '{title}'")
                return {}

            # Disambiguate by director (handles remakes); else most popular.
            chosen, chosen_dir = None, ""
            if creator:
                for cand in sorted(results, key=lambda r: -r.get("popularity", 0))[:5]:
                    dname = await _director(client, cand["id"], key)
                    if _director_matches(dname, creator):
                        chosen, chosen_dir = cand, dname
                        break
            if chosen is None:
                chosen = max(results, key=lambda r: r.get("popularity", 0))
                chosen_dir = await _director(client, chosen["id"], key)

            details = (
                await client.get(f"{TMDB}/movie/{chosen['id']}", params={"api_key": key})
            ).json()
            poster = details.get("poster_path")
            return {
                "title": details.get("title", ""),
                "creators": [chosen_dir] if chosen_dir else [],
                "description": details.get("overview", ""),
                "categories": [g["name"] for g in details.get("genres", [])],
                "average_rating": details.get("vote_average"),
                "published_date": details.get("release_date", ""),
                "cover_image_url": f"{POSTER_BASE}{poster}" if poster else "",
            }
        except Exception as e:
            logger.warning(f"TMDB API error for '{title}': {e}")
            return {}
