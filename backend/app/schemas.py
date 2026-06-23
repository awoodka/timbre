from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.dimensions import FELT_KEYS


class MediaCreate(BaseModel):
    medium: str = "book"
    title: str
    creator: str
    external_id: str | None = None
    cover_image_url: str | None = None
    metadata: dict | None = None


class MediaResponse(BaseModel):
    id: UUID
    medium: str
    title: str
    creator: str
    external_id: str | None
    description: str | None
    cover_image_url: str | None
    metadata: dict | None
    emotion_vector: list[float] | None
    emotion_breakdown: dict | None
    analysis_status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_item(cls, item) -> "MediaResponse":
        return cls(
            id=item.id,
            medium=item.medium,
            title=item.title,
            creator=item.creator,
            external_id=item.external_id,
            description=item.description,
            cover_image_url=item.cover_image_url,
            metadata=item.metadata_,
            emotion_vector=list(item.emotion_vector) if item.emotion_vector is not None else None,
            emotion_breakdown=item.emotion_breakdown,
            analysis_status=item.analysis_status,
            created_at=item.created_at,
        )


class ReasonOut(BaseModel):
    key: str
    name: str
    # "feeling" = an emotion the rec delivers; "ending" = how it lands (experience search).
    kind: Literal["feeling", "ending"] = "feeling"


class MediaSimilarResponse(BaseModel):
    item: MediaResponse
    similarity: float
    reasons: list[ReasonOut] = []


class RecommendResponse(BaseModel):
    gated: bool = False        # true when the user hasn't logged enough works yet
    logged: int = 0
    needed: int = 0
    recommendations: list[MediaSimilarResponse] = []


class RecommendRequest(BaseModel):
    # Recommendations are computed from the user's stored feedback (server-side),
    # so the body only carries how many to return.
    limit: int = Field(default=10, ge=1, le=50)

    # ---- Experience search (all optional; absent ⇒ legacy pure-taste mode) ----
    # Compose the experience you want: feelings to seek (+1) / avoid (-1), how it
    # should land, and how much to lean on this mood vs. your usual taste.
    mood: dict[str, Literal[-1, 1]] | None = None
    ending: Literal["any", "bleak", "bittersweet", "uplifting"] = "any"
    alpha: float = Field(default=0.6, ge=0.0, le=1.0)  # 1.0 = all mood, 0.0 = all taste
    # Optional medium filter (book/film/show/anime/manga/game) — powers per-medium rows.
    medium: str | None = None

    @field_validator("mood")
    @classmethod
    def _felt_keys_only(cls, v: dict | None) -> dict | None:
        if v is None:
            return v
        bad = sorted(k for k in v if k not in FELT_KEYS)
        if bad:
            raise ValueError(f"not felt-emotion keys: {bad}")
        return v


class DimensionResponse(BaseModel):
    key: str
    name: str
    description: str


# ---- Auth / users ----

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=200)
    display_name: str | None = Field(default=None, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    display_name: str | None
    settings: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    settings: dict | None = None


# ---- Per-user ratings ----

class RatingUpsert(BaseModel):
    # {emotion_key: -2…+2} on a 5-point preference scale (not-for-me … loved);
    # neutral (0) emotions are omitted.
    feedback: dict[str, Literal[-2, -1, 1, 2]]

    @field_validator("feedback")
    @classmethod
    def _felt_keys_only(cls, v: dict) -> dict:
        bad = sorted(k for k in v if k not in FELT_KEYS)
        if bad:
            raise ValueError(f"not felt-emotion keys: {bad}")
        return v


class RatingResponse(BaseModel):
    media_id: UUID
    feedback: dict[str, int]
    resonance: float

    model_config = {"from_attributes": True}


class SavedItemResponse(BaseModel):
    media_id: UUID

    model_config = {"from_attributes": True}
