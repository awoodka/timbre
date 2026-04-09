"""
Gather rich emotional context about a book from multiple sources:
1. Google Books API — description, categories, publisher info
2. Web search + scrape — literary analysis essays, emotional reviews
3. Reddit — reader emotional reactions and discussion threads
"""

import asyncio
import logging
import re

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

logger = logging.getLogger(__name__)

SCRAPE_TIMEOUT = 10
MAX_ESSAY_LENGTH = 3000  # chars per scraped essay
MAX_ESSAYS = 4
MAX_REDDIT_THREADS = 3
MAX_COMMENTS_PER_THREAD = 15
MAX_COMMENT_LENGTH = 1500  # chars per comment


async def fetch_google_books(title: str, author: str) -> dict:
    """Fetch book info from Google Books API (free, no key required)."""
    query = f"{title} {author}"
    url = "https://www.googleapis.com/books/v1/volumes"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params={"q": query, "maxResults": 1})
            resp.raise_for_status()
            data = resp.json()

            if not data.get("items"):
                logger.info(f"Google Books: no results for '{query}'")
                return {}

            info = data["items"][0]["volumeInfo"]
            # Get the best available cover image
            image_links = info.get("imageLinks", {})
            cover_url = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
            # Google returns http URLs — upgrade to https
            if cover_url.startswith("http://"):
                cover_url = "https://" + cover_url[7:]

            return {
                "title": info.get("title", ""),
                "authors": info.get("authors", []),
                "description": info.get("description", ""),
                "categories": info.get("categories", []),
                "average_rating": info.get("averageRating"),
                "page_count": info.get("pageCount"),
                "published_date": info.get("publishedDate", ""),
                "cover_image_url": cover_url,
            }
        except Exception as e:
            logger.warning(f"Google Books API error: {e}")
            return {}


async def _scrape_page(client: httpx.AsyncClient, url: str) -> str:
    """Fetch a URL and extract the main text content."""
    try:
        resp = await client.get(
            url,
            follow_redirects=True,
            timeout=SCRAPE_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TimbreBot/1.0)"},
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()

        # Extract text from article or main content area
        article = soup.find("article") or soup.find("main") or soup.find("body")
        if not article:
            return ""

        text = article.get_text(separator=" ", strip=True)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text[:MAX_ESSAY_LENGTH]
    except Exception as e:
        logger.debug(f"Failed to scrape {url}: {e}")
        return ""


async def search_and_scrape_essays(title: str, author: str) -> list[dict]:
    """Search for literary analysis and emotional reviews, scrape the top results."""
    queries = [
        f'"{title}" {author} emotional analysis essay',
        f'"{title}" {author} how it feels to read review mood atmosphere',
    ]

    urls_seen = set()
    results = []

    ddgs = DDGS()
    for query in queries:
        try:
            search_results = list(ddgs.text(query, max_results=5))
            for r in search_results:
                url = r.get("href", "")
                if url and url not in urls_seen and "reddit.com" not in url:
                    urls_seen.add(url)
                    results.append({
                        "url": url,
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                    })
        except Exception as e:
            logger.warning(f"Search error for '{query}': {e}")

    # Scrape the top results
    async with httpx.AsyncClient() as client:
        tasks = [_scrape_page(client, r["url"]) for r in results[:MAX_ESSAYS + 2]]
        scraped = await asyncio.gather(*tasks)

    essays = []
    for r, text in zip(results, scraped):
        if len(text) > 200:
            essays.append({
                "source_url": r["url"],
                "source_title": r["title"],
                "content": text,
            })
            if len(essays) >= MAX_ESSAYS:
                break

    logger.info(f"Scraped {len(essays)} essays for '{title}'")
    return essays


def _extract_comments(data: dict, depth: int = 0) -> list[str]:
    """Recursively extract comment text from Reddit JSON response."""
    comments = []
    if not isinstance(data, dict):
        return comments

    kind = data.get("kind")

    if kind == "Listing":
        for child in data.get("data", {}).get("children", []):
            comments.extend(_extract_comments(child, depth))

    elif kind == "t3":
        # Post body (selftext)
        selftext = data.get("data", {}).get("selftext", "")
        if selftext and len(selftext) > 50:
            comments.append(selftext[:MAX_COMMENT_LENGTH])

    elif kind == "t1":
        # Comment
        body = data.get("data", {}).get("body", "")
        if body and len(body) > 30 and body != "[deleted]" and body != "[removed]":
            comments.append(body[:MAX_COMMENT_LENGTH])
        # Recurse into replies
        replies = data.get("data", {}).get("replies", "")
        if isinstance(replies, dict):
            comments.extend(_extract_comments(replies, depth + 1))

    return comments


async def _fetch_reddit_thread(client: httpx.AsyncClient, url: str) -> dict | None:
    """Fetch a Reddit thread via JSON API and extract comments."""
    # Convert to old.reddit.com JSON endpoint
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

        # Extract post title
        post_title = ""
        try:
            post_title = data[0]["data"]["children"][0]["data"]["title"]
        except (KeyError, IndexError):
            pass

        # Extract all comments
        all_comments = []
        for listing in data:
            all_comments.extend(_extract_comments(listing))

        if not all_comments:
            return None

        # Take the most substantive comments (sort by length)
        all_comments.sort(key=len, reverse=True)
        top_comments = all_comments[:MAX_COMMENTS_PER_THREAD]

        return {
            "thread_title": post_title,
            "thread_url": url,
            "comments": top_comments,
        }
    except Exception as e:
        logger.debug(f"Failed to fetch Reddit thread {url}: {e}")
        return None


async def search_reddit(title: str, author: str) -> list[dict]:
    """Search for Reddit discussions about the book's emotional impact."""
    queries = [
        f'site:reddit.com "{title}" {author} how did it make you feel',
        f'site:reddit.com "{title}" {author} emotional reading experience',
    ]

    urls_seen = set()
    thread_urls = []

    ddgs = DDGS()
    for query in queries:
        try:
            search_results = list(ddgs.text(query, max_results=5))
            for r in search_results:
                url = r.get("href", "")
                # Only keep actual Reddit thread URLs (not user pages, wiki, etc.)
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

    # Fetch threads via JSON API
    async with httpx.AsyncClient() as client:
        tasks = [
            _fetch_reddit_thread(client, url)
            for url in thread_urls[:MAX_REDDIT_THREADS + 2]
        ]
        results = await asyncio.gather(*tasks)

    threads = [r for r in results if r is not None][:MAX_REDDIT_THREADS]
    total_comments = sum(len(t["comments"]) for t in threads)
    logger.info(
        f"Reddit: {len(threads)} threads, {total_comments} comments for '{title}'"
    )
    return threads


async def gather_book_context(title: str, author: str) -> dict:
    """Gather all available context about a book from external sources."""
    google_books, essays, reddit = await asyncio.gather(
        fetch_google_books(title, author),
        search_and_scrape_essays(title, author),
        search_reddit(title, author),
    )

    return {
        "google_books": google_books,
        "essays": essays,
        "reddit": reddit,
    }
