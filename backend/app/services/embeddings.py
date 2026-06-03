"""Corpus-level embedding maintenance.

Stored emotion vectors are *standardized* — mean-centered against the corpus
centroid so cosine similarity reflects what distinguishes a work rather than the
dark/heavy baseline most of the corpus shares.

Because the centroid depends on the whole corpus, every change to the set of
scored works re-standardizes all vectors so they stay in one consistent space.
This is pure arithmetic on stored scores (no LLM calls), so it's cheap to run on
every add. For a much larger corpus this should be optimized (freeze the centroid
and re-standardize in batches); fine as-is for the current scale.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import MediaItem
from app.services.emotional_analysis import compute_centroid, standardize_vector

logger = logging.getLogger(__name__)


async def recompute_all_embeddings(session: AsyncSession) -> int:
    """Rebuild every book's standardized emotion_vector from its stored scores.

    Recomputes the centroid from the current corpus, then sets each vector to
    normalize(scores - centroid). Returns the number of books restandardized.
    """
    items = (
        await session.execute(
            select(MediaItem).where(MediaItem.emotion_breakdown.isnot(None))
        )
    ).scalars().all()
    if not items:
        return 0

    centroid = compute_centroid([m.emotion_breakdown for m in items])
    for m in items:
        m.emotion_vector = standardize_vector(m.emotion_breakdown, centroid)
    await session.commit()

    logger.info(f"Re-standardized {len(items)} embeddings against corpus centroid")
    return len(items)
