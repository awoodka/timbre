import json
import logging

import numpy as np
from google import genai
from google.genai import types

from app.config import settings
from app.dimensions import EMOTIONAL_DIMENSIONS, DIMENSION_KEYS
from app.services.sources import gather_context, MEDIUM_NOUNS

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)

MODEL = "gemini-2.5-flash"


def _build_context_block(context: dict) -> str:
    """Format gathered context into a text block for the LLM prompt."""
    sections = []

    meta = context.get("metadata", {})
    if meta.get("description"):
        sections.append(f"## Description\n{meta['description']}")
    if meta.get("categories"):
        sections.append(f"## Categories\n{', '.join(meta['categories'])}")

    for i, essay in enumerate(context.get("essays", []), 1):
        sections.append(
            f"## Critical/Analysis Excerpt {i} (from: {essay['source_title']})\n"
            f"{essay['content']}"
        )

    reddit_threads = context.get("reddit", [])
    if reddit_threads:
        reactions = [f"- {c}" for t in reddit_threads for c in t["comments"]]
        if reactions:
            sections.append(
                "## Audience Emotional Reactions (from Reddit discussions)\n"
                + "\n".join(reactions)
            )

    if not sections:
        return "(No external context was found for this work.)"
    return "\n\n".join(sections)


async def generate_emotional_profile(
    medium: str, title: str, creator: str, context: dict
) -> str:
    """Step 1: Synthesize a dominant-signature emotional profile from context."""
    noun = MEDIUM_NOUNS.get(medium, medium)
    context_block = _build_context_block(context)
    # For audio-visual media, the craft itself carries emotion — fold it into the
    # felt scoring (Decision §6: aesthetics feed the shared dims, not new ones).
    if medium in {"film", "show", "anime"}:
        craft_hint = (
            "\nThis medium's craft shapes the feeling: account for how cinematography, "
            "color, lighting, music/score, sound, editing rhythm, and performance "
            "contribute to the emotional experience.\n"
        )
    elif medium == "game":
        craft_hint = (
            "\nThis medium's craft shapes the feeling: account for gameplay and player "
            "agency/control, challenge and mastery, immersion/presence, interactivity, "
            "and the music, art, and sound.\n"
        )
    elif medium == "manga":
        craft_hint = (
            "\nThis medium's craft shapes the feeling: account for the art style, "
            "linework, paneling and page rhythm, and use of black and negative space.\n"
        )
    else:
        craft_hint = ""

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=f"""You are distilling the DOMINANT emotional signature and ARC of the {noun} "{title}" by {creator} — what it characteristically feels like to experience — for use in an emotional fingerprint.

Below is context gathered from multiple sources. Use it together with your own knowledge of the work.

--- GATHERED CONTEXT ---
{context_block}
--- END CONTEXT ---
{craft_hint}
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
    medium: str, title: str, creator: str, profile: str
) -> dict[str, float]:
    """Step 2: Score the work on each emotional dimension given the profile."""
    noun = MEDIUM_NOUNS.get(medium, medium)
    dimensions_text = "\n".join(
        f'- **{d["key"]}** ({d["name"]}): {d["description"]}'
        for d in EMOTIONAL_DIMENSIONS
    )
    dimension_properties = {
        key: {"type": "number", "description": f"Score for {key} (0.0 to 1.0)"}
        for key in DIMENSION_KEYS
    }

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=f"""Given this emotional profile of the {noun} "{title}" by {creator}:

---
{profile}
---

Score the {noun} on each dimension below from 0.0 to 1.0 by HOW MUCH THAT QUALITY DEFINES THE OVERALL, SUSTAINED experience — not whether it merely appears at some point.

Anchors (for the emotion dimensions):
- 0.0 = absent
- 0.2 = appears in a few moments but is NOT characteristic
- 0.5 = a recurring, noticeable part of the experience
- 0.8 = a dominant, pervasive quality
- 1.0 = overwhelmingly the defining emotion

Be sparse: a transient moment never justifies a high score. Usually only 4-7 emotion dimensions exceed 0.5; the rest should be 0.3 or below.

Several dimensions are BIPOLAR AXES, not present/absent emotions — for these, 0.5 means typical/neutral and you score the work's POSITION on the axis exactly as its description defines 0.0 vs 1.0 (do NOT default them high): pacing, emotional_complexity, predictability, catharsis, emotional_trajectory, ending_valence.

Dimensions:
{dimensions_text}

Score the audience's felt experience, not the plot. Be precise (0.45 ≠ 0.5).
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
    return {key: max(0.0, min(1.0, float(scores.get(key, 0.0)))) for key in DIMENSION_KEYS}


def normalize_vector(scores: dict[str, float]) -> list[float]:
    """Convert scores dict to a normalized unit vector in dimension order.

    Provisional (un-standardized) vector — used so a freshly analyzed item is never
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


async def analyze_media(medium: str, title: str, creator: str) -> dict:
    """Full pipeline: gather context → synthesize profile → score → normalize."""
    logger.info(f"Gathering context for the {medium} '{title}' by {creator}...")
    context = await gather_context(medium, title, creator)

    sources_found = []
    if context["metadata"].get("description"):
        sources_found.append("metadata")
    sources_found.append(f"{len(context['essays'])} essays")
    reddit_comments = sum(len(t["comments"]) for t in context.get("reddit", []))
    sources_found.append(
        f"{len(context.get('reddit', []))} reddit threads ({reddit_comments} comments)"
    )
    logger.info(f"Context gathered: {', '.join(sources_found)}")

    logger.info(f"Generating emotional profile for '{title}'...")
    profile = await generate_emotional_profile(medium, title, creator, context)

    logger.info(f"Scoring emotional dimensions for '{title}'...")
    scores = await score_emotional_dimensions(medium, title, creator, profile)

    vector = normalize_vector(scores)

    return {
        "description": profile,
        "emotion_breakdown": scores,
        "emotion_vector": vector,
        "cover_image_url": context["metadata"].get("cover_image_url", ""),
        "raw_response": json.dumps(
            {
                "medium": medium,
                "sources": {
                    "metadata": context["metadata"],
                    "essays_scraped": [
                        {"url": e["source_url"], "title": e["source_title"]}
                        for e in context["essays"]
                    ],
                    "reddit_threads": [
                        {"url": t["thread_url"], "title": t["thread_title"],
                         "comment_count": len(t["comments"])}
                        for t in context.get("reddit", [])
                    ],
                },
                "profile": profile,
                "scores": scores,
            },
            indent=2,
        ),
    }
