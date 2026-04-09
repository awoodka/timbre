import asyncio
import logging
import uuid

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dimensions import DIMENSION_KEYS
from app.models.book import Book
from app.schemas import (
    BookCreate,
    BookResponse,
    BookSimilarResponse,
    RecommendRequest,
)
from app.services.emotional_analysis import analyze_book, normalize_vector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/books", tags=["books"])


async def _run_analysis(book_id: uuid.UUID, title: str, author: str, db_url: str):
    """Background task to run emotional analysis on a book."""
    from app.database import async_session

    try:
        result = await analyze_book(title, author)
        async with async_session() as session:
            book = await session.get(Book, book_id)
            if book:
                book.description = result["description"]
                book.emotion_breakdown = result["emotion_breakdown"]
                book.emotion_vector = result["emotion_vector"]
                book.raw_claude_response = result["raw_response"]
                book.analysis_status = "completed"
                await session.commit()
    except Exception as e:
        logger.error(f"Analysis failed for {title}: {e}")
        async with async_session() as session:
            book = await session.get(Book, book_id)
            if book:
                book.analysis_status = "failed"
                book.raw_claude_response = str(e)
                await session.commit()


@router.post("", response_model=BookResponse, status_code=201)
async def create_book(
    book_in: BookCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    book = Book(
        title=book_in.title,
        author=book_in.author,
        isbn=book_in.isbn,
        cover_image_url=book_in.cover_image_url,
        metadata_=book_in.metadata,
        analysis_status="pending",
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)

    background_tasks.add_task(
        _run_analysis, book.id, book.title, book.author, ""
    )

    return BookResponse.from_orm_book(book)


@router.get("", response_model=list[BookResponse])
async def list_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).order_by(Book.created_at.desc()))
    books = result.scalars().all()
    return [BookResponse.from_orm_book(b) for b in books]


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookResponse.from_orm_book(book)


@router.get("/{book_id}/similar", response_model=list[BookSimilarResponse])
async def get_similar_books(
    book_id: uuid.UUID,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.emotion_vector is None:
        raise HTTPException(status_code=400, detail="Book has not been analyzed yet")

    vector_str = "[" + ",".join(str(v) for v in book.emotion_vector) + "]"
    query = text(
        """
        SELECT id, 1 - (emotion_vector <=> CAST(:vec AS vector)) as similarity
        FROM books
        WHERE id != :book_id AND emotion_vector IS NOT NULL
        ORDER BY emotion_vector <=> CAST(:vec AS vector)
        LIMIT :lim
        """
    )
    result = await db.execute(
        query, {"vec": vector_str, "book_id": str(book_id), "lim": limit}
    )
    rows = result.fetchall()

    similar = []
    for row in rows:
        sim_book = await db.get(Book, row[0])
        similar.append(
            BookSimilarResponse(
                book=BookResponse.from_orm_book(sim_book),
                similarity=round(float(row[1]), 4),
            )
        )
    return similar


@router.post("/{book_id}/reanalyze", response_model=BookResponse)
async def reanalyze_book(
    book_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.analysis_status = "pending"
    await db.commit()

    background_tasks.add_task(_run_analysis, book.id, book.title, book.author, "")

    await db.refresh(book)
    return BookResponse.from_orm_book(book)
