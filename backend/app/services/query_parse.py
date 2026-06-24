"""Natural-language search: turn a free-text description of a desired experience
into the same structured query the experience-search recommender already consumes
(feelings to seek/avoid + an ending tone + an optional medium).

This is a thin *translation* layer over Gemini 2.5 Flash — it never sees the corpus
and never names a title, so it cannot hallucinate a recommendation. It only sets the
dials; all ranking stays the deterministic vector math in routers/recommend.py.
"""

import json
import logging

from google.genai import types

from app.dimensions import EMOTIONAL_DIMENSIONS, FELT_KEYS
from app.services.emotional_analysis import MODEL, client

logger = logging.getLogger(__name__)

_FELT_SET = set(FELT_KEYS)
_ENDINGS = ("any", "bleak", "bittersweet", "uplifting")
_MEDIA = {"book", "film", "show", "anime", "manga", "game"}
_MAX_PICKS = 6  # keep the mood vector crisp — only the dominant feelings

# Felt-emotion vocabulary (name + description) so Flash maps fuzzy language and
# situations onto the real dimensions accurately.
_FELT_VOCAB = "\n".join(
    f'- {d["key"]} ({d["name"]}): {d["description"]}'
    for d in EMOTIONAL_DIMENSIONS
    if d["key"] in _FELT_SET
)

_PARSE_SCHEMA = {
    "type": "object",
    "properties": {
        "seek": {"type": "array", "items": {"type": "string", "enum": FELT_KEYS}},
        "avoid": {"type": "array", "items": {"type": "string", "enum": FELT_KEYS}},
        "ending": {"type": "string", "enum": list(_ENDINGS)},
        "medium": {"type": "string", "enum": ["any", *sorted(_MEDIA)]},
    },
    "required": ["seek", "avoid", "ending", "medium"],
}

_EMPTY = {"mood": {}, "ending": "any", "medium": None}


def _prompt(description: str) -> str:
    return f"""You translate a person's free-text description of what they're in the mood to read, watch, or play into a structured emotional query for a cross-media recommender.

The description may name feelings ("cozy but a little sad"), a situation or occasion ("something for a rainy Sunday", "after a breakup", "to watch with my mom"), or both. Infer the EMOTIONAL EXPERIENCE they're after — map situations to feelings (e.g. "rainy Sunday" -> stillness, melancholy, warmth; "sleepless and on edge" -> tension, dread, frenetic_energy).

Choose ONLY from these felt-emotion keys (use the key verbatim):
{_FELT_VOCAB}

Return a JSON object:
- "seek": the emotions they want to feel — only the DOMINANT few (about 2-4). Order by importance.
- "avoid": emotions they clearly want to steer clear of. Usually empty; never invent one.
- "ending": how they want it to land — "uplifting", "bleak", "bittersweet", or "any" if unstated.
- "medium": "book", "film", "show", "anime", "manga", or "game" only if they name one; otherwise "any".

If the text expresses no discernible feeling or intent, return empty "seek" and "avoid", "any", "any".

Description:
\"\"\"{description}\"\"\""""


async def parse_query(description: str) -> dict:
    """Parse a natural-language description -> {mood: {felt_key: ±1}, ending, medium}.

    `mood` is the seek/avoid map `build_mood_vector` expects. Any failure (Gemini
    error, bad JSON) degrades to an empty query so the caller returns no results
    rather than 500-ing.
    """
    description = (description or "").strip()
    if not description:
        return dict(_EMPTY)
    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=_prompt(description),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_PARSE_SCHEMA,
                temperature=0.2,
            ),
        )
        data = json.loads(response.text)
    except Exception:
        logger.exception("Natural-language query parse failed")
        return dict(_EMPTY)

    seek = [k for k in data.get("seek", []) if k in _FELT_SET][:_MAX_PICKS]
    seen = set(seek)
    avoid = [k for k in data.get("avoid", []) if k in _FELT_SET and k not in seen][:_MAX_PICKS]

    mood = {k: 1 for k in seek}
    for k in avoid:
        mood[k] = -1

    ending = data.get("ending", "any")
    if ending not in _ENDINGS:
        ending = "any"

    medium = data.get("medium", "any")
    medium = medium if medium in _MEDIA else None

    return {"mood": mood, "ending": ending, "medium": medium}
