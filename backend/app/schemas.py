from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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


class MediaSimilarResponse(BaseModel):
    item: MediaResponse
    similarity: float


class RatingInput(BaseModel):
    media_id: UUID
    rating: float = Field(ge=1, le=5)


class RecommendRequest(BaseModel):
    ratings: list[RatingInput]
    limit: int = Field(default=10, ge=1, le=50)


class DimensionResponse(BaseModel):
    key: str
    name: str
    description: str
