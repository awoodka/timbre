"""Shared discourse scraping for any medium.

Searches the web for emotional analysis/reviews and Reddit reactions about a
work, adapting the query wording to the medium (the `noun` argument, e.g. "film",
"video game"). Medium-agnostic: only the search phrasing changes.
"""

import asyncio
import logging
import re

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

logger = logging.getLogger(__name__)

SCRAPE_TIMEOUT = 10
MAX_ESSAY_LENGTH = 3000
MAX_ESSAYS = 4
MAX_REDDIT_THREADS = 3
MAX_COMMENTS_PER_THREAD = 15
MAX_COMMENT_LENGTH = 1500


async def _scrape_page(client: httpx.AsyncClient, url: str) -> str:
    try:
        resp = await client.get(
            url,
            follow_redirects=True,
            timeout=SCRAPE_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TimbreBot/1.0)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()
        article = soup.find("article") or soup.find("main") or soup.find("body")
        if not article:
            return ""
        text = re.sub(r"\s+", " ", article.get_text(separator=" ", strip=True)).strip()
        return text[:MAX_ESSAY_LENGTH]
    except Exception as e:
        logger.debug(f"Failed to scrape {url}: {e}")
        return ""


async def search_and_scrape_essays(title: str, creator: str, noun: str) -> list[dict]:
    """Search for emotional analysis / reviews of the work and scrape top results."""
    queries = [
        f'"{title}" {creator} {noun} emotional analysis',
        f'"{title}" {creator} how it feels {noun} mood atmosphere review',
    ]

    urls_seen = set()
    results = []
    ddgs = DDGS()
    for query in queries:
        try:
            for r in list(ddgs.text(query, max_results=5)):
                url = r.get("href", "")
                if url and url not in urls_seen and "reddit.com" not in url:
                    urls_seen.add(url)
                    results.append({"url": url, "title": r.get("title", "")})
        except Exception as e:
            logger.warning(f"Search error for '{query}': {e}")

    async with httpx.AsyncClient() as client:
        scraped = await asyncio.gather(
            *[_scrape_page(client, r["url"]) for r in results[: MAX_ESSAYS + 2]]
        )

    essays = []
    for r, text in zip(results, scraped):
        if len(text) > 200:
            essays.append(
                {"source_url": r["url"], "source_title": r["title"], "content": text}
            )
            if len(essays) >= MAX_ESSAYS:
                break
    logger.info(f"Scraped {len(essays)} essays for '{title}'")
    return essays


def _extract_comments(data: dict, depth: int = 0) -> list[str]:
    comments = []
    if not isinstance(data, dict):
        return comments
    kind = data.get("kind")
    if kind == "Listing":
        for child in data.get("data", {}).get("children", []):
            comments.extend(_extract_comments(child, depth))
    elif kind == "t3":
        selftext = data.get("data", {}).get("selftext", "")
        if selftext and len(selftext) > 50:
            comments.append(selftext[:MAX_COMMENT_LENGTH])
    elif kind == "t1":
        body = data.get("data", {}).get("body", "")
        if body and len(body) > 30 and body not in ("[deleted]", "[removed]"):
            comments.append(body[:MAX_COMMENT_LENGTH])
        replies = data.get("data", {}).get("replies", "")
        if isinstance(replies, dict):
            comments.extend(_extract_comments(replies, depth + 1))
    return comments


async def _fetch_reddit_thread(client: httpx.AsyncClient, url: str) -> dict | None:
    json_url = re.sub(r"(https?://)(?:www\.)?reddit\.com", r"\1www.reddit.com", url)
    if "?" in json_url:
        json_url = json_url.split("?")[0]
    json_url = json_url.rstrip("/") + ".json"
    try:
        resp = await client.get(
            json_url,
            timeout=SCRAPE_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TimbreBot/1.0)"},
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list) or len(data) < 2:
            return None
        try:
            post_title = data[0]["data"]["children"][0]["data"]["title"]
        except (KeyError, IndexError):
            post_title = ""
        all_comments = []
        for listing in data:
            all_comments.extend(_extract_comments(listing))
        if not all_comments:
            return None
        all_comments.sort(key=len, reverse=True)
        return {
            "thread_title": post_title,
            "thread_url": url,
            "comments": all_comments[:MAX_COMMENTS_PER_THREAD],
        }
    except Exception as e:
        logger.debug(f"Failed to fetch Reddit thread {url}: {e}")
        return None


async def search_reddit(title: str, creator: str, noun: str) -> list[dict]:
    """Search Reddit for discussion of the work's emotional impact."""
    queries = [
        f'site:reddit.com "{title}" {creator} how did it make you feel',
        f'site:reddit.com "{title}" {creator} emotional {noun} experience',
    ]
    urls_seen = set()
    thread_urls = []
    ddgs = DDGS()
    for query in queries:
        try:
            for r in list(ddgs.text(query, max_results=5)):
                url = r.get("href", "")
                if (
                    url
                    and "reddit.com/r/" in url
                    and "/comments/" in url
                    and url not in urls_seen
                ):
                    urls_seen.add(url)
                    thread_urls.append(url)
        except Exception as e:
            logger.warning(f"Reddit search error for '{query}': {e}")

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_fetch_reddit_thread(client, u) for u in thread_urls[: MAX_REDDIT_THREADS + 2]]
        )

    threads = [r for r in results if r is not None][:MAX_REDDIT_THREADS]
    total = sum(len(t["comments"]) for t in threads)
    logger.info(f"Reddit: {len(threads)} threads, {total} comments for '{title}'")
    return threads
