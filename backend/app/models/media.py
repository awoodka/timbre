import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.dimensions import NUM_DIMENSIONS


class MediaItem(Base):
    """A single work of any medium (book, film, show, game, ...).

    The emotional pipeline is medium-agnostic; `medium` selects the context
    source and tunes prompt wording. Medium-specific fields live in `metadata_`.
    """

    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    medium: Mapped[str] = mapped_column(String(20), nullable=False, default="book")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    creator: Mapped[str] = mapped_column(String(500), nullable=False)
    # External source id (ISBN for books, TMDB id for films, etc.)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    emotion_vector: Mapped[list | None] = mapped_column(
        Vector(NUM_DIMENSIONS), nullable=True
    )
    emotion_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
