import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, JSON, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """An account: login credentials + a flexible profile-settings blob.

    Login is by `username` (unique). `settings` is intentionally schema-free JSON
    so new preferences can be added without a migration. Ratings live in their own
    table, one row per (user, media), and are owned by the user.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    ratings: Mapped[list["Rating"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Rating(Base):
    """A user's per-emotion feedback on a media item — which felt emotions they
    liked (+1) / disliked (-1) — plus a derived overall `resonance`. One per (user, media)."""

    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("user_id", "media_id", name="uq_user_media"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # {emotion_key: +1 (liked) | -1 (disliked)}; unmarked emotions are omitted (neutral).
    feedback: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Derived overall score in [0,1] (server-computed from feedback); for sort/display.
    resonance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="ratings")
