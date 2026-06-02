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
        contents=f"""You are distilling the DOMINANT emotional signature and ARC of "{title}" by {author} — what it characteristically feels like to read — for use in an emotional fingerprint.

Below is context gathered from multiple sources. Use it together with your own knowledge of the work.

--- GATHERED CONTEXT ---
{context_block}
--- END CONTEXT ---

Write 2 short paragraphs (felt experience, not plot) capturing:
- the DOMINANT, sustained emotional texture — what pervades the experience, its center of gravity; and
- the ARC: the direction the feeling travels (does it descend, rise, hold, or oscillate?) and how it RESOLVES — the aftertaste it leaves.

Capture the SHAPE of the experience, not a beat-by-beat recap. A work passes through many fleeting feelings — mention a transient one only if you explicitly flag it as occasional, not characteristic.

Then end with exactly these two lines:
Dominant emotions: <3-6 emotions, most dominant first>
Arc & resolution: <one line: where it starts emotionally → where it lands>""",
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

Score the book on each dimension below from 0.0 to 1.0 by HOW MUCH THAT QUALITY DEFINES THE OVERALL, SUSTAINED reading experience — not whether it merely appears at some point.

Anchors (for the emotion dimensions):
- 0.0 = absent
- 0.2 = appears in a few moments but is NOT characteristic
- 0.5 = a recurring, noticeable part of the experience
- 0.8 = a dominant, pervasive quality
- 1.0 = overwhelmingly the defining emotion

Be sparse: a transient scene never justifies a high score. Usually only 4-7 emotion dimensions exceed 0.5; the rest should be 0.3 or below.

Several dimensions are BIPOLAR AXES, not present/absent emotions — for these, 0.5 means typical/neutral and you score the book's POSITION on the axis exactly as its description defines 0.0 vs 1.0 (do NOT default them high): pacing, emotional_complexity, predictability, catharsis, emotional_trajectory, ending_valence.

Dimensions:
{dimensions_text}

Score the reader's felt experience, not the plot. Be precise (0.45 ≠ 0.5).
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
    """Convert scores dict to a normalized unit vector in dimension order.

    Provisional (un-standardized) vector — used so a freshly analyzed book is never
    null. The stored vector is replaced with a standardized one by
    app.services.embeddings.recompute_all_embeddings once scores are persisted.
    """
    vec = np.array([scores[key] for key in DIMENSION_KEYS], dtype=np.float64)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def compute_centroid(breakdowns: list[dict[str, float]]) -> np.ndarray:
    """Mean score per dimension across the corpus — the standardization reference."""
    mat = np.array(
        [[bd.get(key, 0.0) for key in DIMENSION_KEYS] for bd in breakdowns],
        dtype=np.float64,
    )
    return mat.mean(axis=0)


def standardize_vector(scores: dict[str, float], centroid: np.ndarray) -> list[float]:
    """Mean-center scores against the corpus centroid, then unit-normalize.

    Centering removes the shared 'baseline mood' the whole corpus has in common, so
    cosine similarity is driven by what DISTINGUISHES a work — which is what lets the
    space discriminate and lets the arc dimensions actually separate works.
    """
    vec = np.array([scores[key] for key in DIMENSION_KEYS], dtype=np.float64) - centroid
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
