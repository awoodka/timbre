from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str | None = None
    cover_image_url: str | None = None
    metadata: dict | None = None


class EmotionBreakdown(BaseModel):
    model_config = {"extra": "allow"}


class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    isbn: str | None
    description: str | None
    cover_image_url: str | None
    metadata: dict | None
    emotion_vector: list[float] | None
    emotion_breakdown: dict | None
    analysis_status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_book(cls, book) -> "BookResponse":
        return cls(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            description=book.description,
            cover_image_url=book.cover_image_url,
            metadata=book.metadata_,
            emotion_vector=list(book.emotion_vector) if book.emotion_vector is not None else None,
            emotion_breakdown=book.emotion_breakdown,
            analysis_status=book.analysis_status,
            created_at=book.created_at,
        )


class BookSimilarResponse(BaseModel):
    book: BookResponse
    similarity: float


class RatingInput(BaseModel):
    book_id: UUID
    rating: float = Field(ge=1, le=5)


class RecommendRequest(BaseModel):
    ratings: list[RatingInput]
    limit: int = Field(default=10, ge=1, le=50)


class DimensionResponse(BaseModel):
    key: str
    name: str
    description: str
