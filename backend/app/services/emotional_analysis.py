import json
import logging

import numpy as np
from google import genai
from google.genai import types

from app.config import settings
from app.dimensions import EMOTIONAL_DIMENSIONS, DIMENSION_KEYS
from app.services.book_sources import gather_book_context

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)

MODEL = "gemini-2.5-flash"


def _build_context_block(context: dict) -> str:
    """Format gathered context into a text block for the LLM prompt."""
    sections = []

    # Google Books description
    gb = context.get("google_books", {})
    if gb.get("description"):
        sections.append(
            f"## Publisher Description\n{gb['description']}"
        )
    if gb.get("categories"):
        sections.append(f"## Categories\n{', '.join(gb['categories'])}")

    # Scraped essays and analysis
    essays = context.get("essays", [])
    for i, essay in enumerate(essays, 1):
        sections.append(
            f"## Literary Analysis Excerpt {i} (from: {essay['source_title']})\n"
            f"{essay['content']}"
        )

    # Reddit reader reactions
    reddit_threads = context.get("reddit", [])
    if reddit_threads:
        reader_reactions = []
        for thread in reddit_threads:
            for comment in thread["comments"]:
                reader_reactions.append(f"- {comment}")
        if reader_reactions:
            sections.append(
                f"## Reader Emotional Reactions (from Reddit discussions)\n"
                + "\n".join(reader_reactions)
            )

    if not sections:
        return "(No external context was found for this book.)"

    return "\n\n".join(sections)


async def generate_emotional_profile(
    title: str, author: str, context: dict
) -> str:
    """Step 1: Synthesize an emotional profile from all gathered context."""
    context_block = _build_context_block(context)

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=f"""You are creating an emotional profile for "{title}" by {author}.

Below is context gathered from multiple sources — a publisher description, literary analysis essays, and reviews. Use ALL of this material, combined with your own knowledge of the book, to write a rich emotional profile.

--- GATHERED CONTEXT ---
{context_block}
--- END CONTEXT ---

Using the above context and your own knowledge, write an emotional profile of this book.

Do NOT write a plot summary. Instead, describe:
- The dominant emotional texture of reading this book
- How the emotional tone shifts across the arc of the book
- The atmosphere and tone (e.g., oppressive, dreamlike, frenetic, meditative)
- What it FEELS like to read it — the reader's internal experience
- Sensory qualities of the prose (dense, sparse, lyrical, blunt, visceral)
- The emotional aftertaste — what lingers after finishing
- Specific emotional moments or qualities highlighted in the analysis essays

Write 3-4 paragraphs focused entirely on the felt experience, not events. Ground your analysis in the source material where possible.""",
        config=types.GenerateContentConfig(
            max_output_tokens=2000,
            temperature=0.7,
        ),
    )
    return response.text


async def score_emotional_dimensions(
    title: str, author: str, profile: str
) -> dict[str, float]:
    """Step 2: Score the book on each emotional dimension given the profile."""
    dimensions_text = "\n".join(
        f'- **{d["key"]}** ({d["name"]}): {d["description"]}'
        for d in EMOTIONAL_DIMENSIONS
    )

    dimension_properties = {
        key: {
            "type": "number",
            "description": f"Score for {key} (0.0 to 1.0)",
        }
        for key in DIMENSION_KEYS
    }

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=f"""Given this emotional profile of "{title}" by {author}:

---
{profile}
---

Score the book on each of the following emotional dimensions from 0.0 to 1.0, where 0.0 means this emotion is completely absent from the reading experience and 1.0 means it is an overwhelmingly dominant part of the experience.

Dimensions:
{dimensions_text}

IMPORTANT:
- Score based on the READER'S emotional experience, not the book's themes
- Most scores should NOT be extreme — use the full 0.0-1.0 range
- A typical book should have 3-6 dimensions above 0.5 and many near 0.0-0.3
- Be precise: 0.45 is different from 0.5

Return a JSON object with each dimension key mapped to its score.""",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": dimension_properties,
                "required": DIMENSION_KEYS,
            },
            temperature=0.3,
        ),
    )

    scores = json.loads(response.text)

    result = {}
    for key in DIMENSION_KEYS:
        val = float(scores.get(key, 0.0))
        result[key] = max(0.0, min(1.0, val))

    return result


def normalize_vector(scores: dict[str, float]) -> list[float]:
    """Convert scores dict to a normalized unit vector in dimension order."""
    vec = np.array([scores[key] for key in DIMENSION_KEYS], dtype=np.float64)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


async def analyze_book(title: str, author: str) -> dict:
    """Full pipeline: gather context → synthesize profile → score → normalize."""
    # Step 0: Gather context from Google Books + web essays
    logger.info(f"Gathering context for '{title}' by {author}...")
    context = await gather_book_context(title, author)

    sources_found = []
    if context["google_books"].get("description"):
        sources_found.append("google_books")
    sources_found.append(f"{len(context['essays'])} essays")
    reddit_comments = sum(len(t["comments"]) for t in context.get("reddit", []))
    sources_found.append(f"{len(context.get('reddit', []))} reddit threads ({reddit_comments} comments)")
    logger.info(f"Context gathered: {', '.join(sources_found)}")

    # Step 1: Synthesize emotional profile from all sources
    logger.info(f"Generating emotional profile for '{title}'...")
    profile = await generate_emotional_profile(title, author, context)

    # Step 2: Score emotional dimensions
    logger.info(f"Scoring emotional dimensions for '{title}'...")
    scores = await score_emotional_dimensions(title, author, profile)

    # Step 3: Normalize to unit vector
    vector = normalize_vector(scores)

    return {
        "description": profile,
        "emotion_breakdown": scores,
        "emotion_vector": vector,
        "cover_image_url": context["google_books"].get("cover_image_url", ""),
        "raw_response": json.dumps(
            {
                "sources": {
                    "google_books": context["google_books"],
                    "essays_scraped": [
                        {"url": e["source_url"], "title": e["source_title"]}
                        for e in context["essays"]
                    ],
                    "reddit_threads": [
                        {"url": t["thread_url"], "title": t["thread_title"], "comment_count": len(t["comments"])}
                        for t in context.get("reddit", [])
                    ],
                },
                "profile": profile,
                "scores": scores,
            },
            indent=2,
        ),
    }
