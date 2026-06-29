"""Emotional bridge: an on-demand, user-facing explanation of why a work fits a
user's taste — grounded in their emotionally-closest rated works. Reuses the same
Gemini client as the analysis pipeline, but returns plain text (no schema)."""

from google import genai
from google.genai import types

from app.config import settings
from app.dimensions import FELT_KEYS

client = genai.Client(api_key=settings.gemini_api_key)
MODEL = "gemini-2.5-flash"

# How the user's strongest emotion mark on a work reads in prose.
_MARK_WORD = {2: "loved", 1: "liked", -1: "cooled on", -2: "didn't connect with"}


def _top_feelings(breakdown: dict, n: int = 4) -> list[str]:
    """The work's strongest FELT emotions (excludes the bipolar axis dims). Prefers the
    meaningfully-present ones (≥0.3) but always falls back to the top 2, so a work never
    ends up described with no real feelings (no vague "distinct mood" filler)."""
    felt = sorted(
        ((k, v) for k, v in (breakdown or {}).items() if k in FELT_KEYS),
        key=lambda kv: -kv[1],
    )
    if not felt:
        return []
    picked = [k for k, v in felt[:n] if v >= 0.3] or [k for k, _ in felt[:2]]
    return [k.replace("_", " ") for k in picked]


def _neighbor_line(nb: dict) -> str:
    feelings = ", ".join(_top_feelings(nb["emotion_breakdown"])) or "a distinct mood"
    marks = nb.get("feedback") or {}
    if marks:
        verb = _MARK_WORD.get(max(marks.values()), "rated")
    elif nb.get("enjoyment"):
        verb = "loved" if nb["enjoyment"] >= 4 else "liked"
    else:
        verb = "rated"
    return f'- "{nb["title"]}" ({nb["medium"]}) — feels like {feelings}; you {verb} it'


def build_prompt(item, neighbors: list[dict]) -> str:
    target_feelings = ", ".join(_top_feelings(item.emotion_breakdown)) or "a distinct emotional texture"
    neighbor_block = "\n".join(_neighbor_line(n) for n in neighbors)
    return f"""You are Timbre, a recommendation engine that matches books, films, shows, anime, manga, and games by the EMOTIONS they evoke — not by genre.

A reader is looking at "{item.title}" by {item.creator} ({item.medium}). Its strongest felt emotions: {target_feelings}.

Here are works this reader has responded to that are emotionally closest to it:
{neighbor_block}

In 2-3 warm, specific sentences, tell the reader (address them as "you") why "{item.title}" fits their taste — the emotional throughline it shares with one or two of the works above. Name those one or two works. Focus on the FELT experience (the ache, the awe, the tension, the tenderness), not plot or genre. Do not mention numbers, scores, ratings, or "emotional vectors." Output only the explanation, ready to show the reader."""


async def generate_bridge(item, neighbors: list[dict]) -> str:
    """One Gemini Flash call → a short, ready-to-display explanation paragraph.

    `max_output_tokens` is generous on purpose: gemini-2.5-flash *thinks* by default and
    those (invisible) thinking tokens count against this budget — at 400 they ate almost
    all of it and truncated the answer mid-sentence (finish_reason=MAX_TOKENS). The
    installed SDK can't disable thinking, so we just leave ample room for it + the answer."""
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=build_prompt(item, neighbors),
        config=types.GenerateContentConfig(max_output_tokens=2048, temperature=0.8),
    )
    return (response.text or "").strip()
