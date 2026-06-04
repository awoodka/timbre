"""TV-show metadata source: TMDB TV API (requires a free TMDB_API_KEY).

Mirrors film.py. Disambiguates reboots / international versions (e.g. The Office
US/UK, Battlestar Galactica 1978/2004) by matching the showrunner in `created_by`
against the stored `creator`. `created_by` is in /tv/{id} details, so no separate
credits call is needed.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TMDB = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"


def _creator_matches(created_by: list, creator: str) -> bool:
    if not creator or not created_by:
        return False
    c = creator.lower()
    last = c.split()[-1]
    return any(
        n.get("name") and (n["name"].lower() == c or last in n["name"].lower())
        for n in created_by
    )


async def fetch_metadata(title: str, creator: str) -> dict:
    """Return a uniform metadata dict for a TV series via TMDB."""
    key = settings.tmdb_api_key
    if not key:
        logger.warning("TMDB_API_KEY not set; skipping show metadata for '%s'", title)
        return {}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{TMDB}/search/tv", params={"api_key": key, "query": title}
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                logger.info(f"TMDB: no TV results for '{title}'")
                return {}

            candidates = sorted(results, key=lambda r: -r.get("popularity", 0))
            details_cache = {}
            chosen = None

            # /tv/{id} carries created_by + all metadata; pick by showrunner match.
            if creator:
                for cand in candidates[:5]:
                    d = (await client.get(
                        f"{TMDB}/tv/{cand['id']}", params={"api_key": key}
                    )).json()
                    details_cache[cand["id"]] = d
                    if _creator_matches(d.get("created_by", []), creator):
                        chosen = d
                        break
            if chosen is None:
                top = candidates[0]
                chosen = details_cache.get(top["id"]) or (await client.get(
                    f"{TMDB}/tv/{top['id']}", params={"api_key": key}
                )).json()

            poster = chosen.get("poster_path")
            return {
                "title": chosen.get("name", ""),
                "creators": [c["name"] for c in chosen.get("created_by", [])],
                "description": chosen.get("overview", ""),
                "categories": [g["name"] for g in chosen.get("genres", [])],
                "average_rating": chosen.get("vote_average"),
                "published_date": chosen.get("first_air_date", ""),
                "cover_image_url": f"{POSTER_BASE}{poster}" if poster else "",
            }
        except Exception as e:
            logger.warning(f"TMDB TV API error for '{title}': {e}")
            return {}
