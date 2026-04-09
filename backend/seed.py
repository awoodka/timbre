"""
Seed script: populates the database with 50 well-known books.

Usage:
    python -m seed                     # Just insert books (no analysis)
    python -m seed --analyze           # Insert and run emotional analysis via Gemini
"""

import asyncio
import argparse
import logging

from app.database import init_db, async_session
from app.models.book import Book
from app.services.emotional_analysis import analyze_book
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_BOOKS = [
    # --- Literary Fiction (15) ---
    {"title": "The Road", "author": "Cormac McCarthy", "metadata_": {"year": 2006, "genre": ["post-apocalyptic", "literary fiction"]}},
    {"title": "Blood Meridian", "author": "Cormac McCarthy", "metadata_": {"year": 1985, "genre": ["western", "literary fiction"]}},
    {"title": "Norwegian Wood", "author": "Haruki Murakami", "metadata_": {"year": 1987, "genre": ["literary fiction", "romance"]}},
    {"title": "Kafka on the Shore", "author": "Haruki Murakami", "metadata_": {"year": 2002, "genre": ["literary fiction", "magical realism"]}},
    {"title": "No Longer Human", "author": "Osamu Dazai", "metadata_": {"year": 1948, "genre": ["literary fiction", "autobiographical"]}},
    {"title": "Beloved", "author": "Toni Morrison", "metadata_": {"year": 1987, "genre": ["literary fiction", "historical"]}},
    {"title": "Never Let Me Go", "author": "Kazuo Ishiguro", "metadata_": {"year": 2005, "genre": ["science fiction", "literary fiction"]}},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "metadata_": {"year": 1925, "genre": ["literary fiction", "classic"]}},
    {"title": "One Hundred Years of Solitude", "author": "Gabriel Garcia Marquez", "metadata_": {"year": 1967, "genre": ["magical realism", "literary fiction"]}},
    {"title": "The Bell Jar", "author": "Sylvia Plath", "metadata_": {"year": 1963, "genre": ["literary fiction", "autobiographical"]}},
    {"title": "A Little Life", "author": "Hanya Yanagihara", "metadata_": {"year": 2015, "genre": ["literary fiction", "contemporary"]}},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "metadata_": {"year": 1960, "genre": ["literary fiction", "classic"]}},
    {"title": "The God of Small Things", "author": "Arundhati Roy", "metadata_": {"year": 1997, "genre": ["literary fiction", "postcolonial"]}},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "metadata_": {"year": 1951, "genre": ["literary fiction", "coming-of-age"]}},
    {"title": "Normal People", "author": "Sally Rooney", "metadata_": {"year": 2018, "genre": ["literary fiction", "contemporary"]}},

    # --- Science Fiction (7) ---
    {"title": "Project Hail Mary", "author": "Andy Weir", "metadata_": {"year": 2021, "genre": ["science fiction", "adventure"]}},
    {"title": "Dune", "author": "Frank Herbert", "metadata_": {"year": 1965, "genre": ["science fiction", "epic"]}},
    {"title": "Neuromancer", "author": "William Gibson", "metadata_": {"year": 1984, "genre": ["cyberpunk", "science fiction"]}},
    {"title": "The Left Hand of Darkness", "author": "Ursula K. Le Guin", "metadata_": {"year": 1969, "genre": ["science fiction", "literary fiction"]}},
    {"title": "Solaris", "author": "Stanislaw Lem", "metadata_": {"year": 1961, "genre": ["science fiction", "philosophical"]}},
    {"title": "Flowers for Algernon", "author": "Daniel Keyes", "metadata_": {"year": 1966, "genre": ["science fiction", "literary fiction"]}},
    {"title": "Annihilation", "author": "Jeff VanderMeer", "metadata_": {"year": 2014, "genre": ["science fiction", "weird fiction"]}},

    # --- Fantasy (6) ---
    {"title": "The Name of the Wind", "author": "Patrick Rothfuss", "metadata_": {"year": 2007, "genre": ["fantasy", "epic"]}},
    {"title": "Piranesi", "author": "Susanna Clarke", "metadata_": {"year": 2020, "genre": ["fantasy", "literary fiction"]}},
    {"title": "The House in the Cerulean Sea", "author": "TJ Klune", "metadata_": {"year": 2020, "genre": ["fantasy", "cozy"]}},
    {"title": "Circe", "author": "Madeline Miller", "metadata_": {"year": 2018, "genre": ["fantasy", "mythological"]}},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "metadata_": {"year": 1937, "genre": ["fantasy", "adventure"]}},
    {"title": "A Wizard of Earthsea", "author": "Ursula K. Le Guin", "metadata_": {"year": 1968, "genre": ["fantasy", "coming-of-age"]}},

    # --- Horror / Gothic (5) ---
    {"title": "House of Leaves", "author": "Mark Z. Danielewski", "metadata_": {"year": 2000, "genre": ["horror", "experimental"]}},
    {"title": "The Shining", "author": "Stephen King", "metadata_": {"year": 1977, "genre": ["horror", "psychological"]}},
    {"title": "The Haunting of Hill House", "author": "Shirley Jackson", "metadata_": {"year": 1959, "genre": ["horror", "gothic"]}},
    {"title": "Mexican Gothic", "author": "Silvia Moreno-Garcia", "metadata_": {"year": 2020, "genre": ["horror", "gothic"]}},
    {"title": "Frankenstein", "author": "Mary Shelley", "metadata_": {"year": 1818, "genre": ["gothic", "science fiction"]}},

    # --- Dystopian (4) ---
    {"title": "1984", "author": "George Orwell", "metadata_": {"year": 1949, "genre": ["dystopian", "political fiction"]}},
    {"title": "Brave New World", "author": "Aldous Huxley", "metadata_": {"year": 1932, "genre": ["dystopian", "science fiction"]}},
    {"title": "The Handmaid's Tale", "author": "Margaret Atwood", "metadata_": {"year": 1985, "genre": ["dystopian", "literary fiction"]}},
    {"title": "Fahrenheit 451", "author": "Ray Bradbury", "metadata_": {"year": 1953, "genre": ["dystopian", "science fiction"]}},

    # --- Absurdist / Dark Humor (3) ---
    {"title": "The Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams", "metadata_": {"year": 1979, "genre": ["science fiction", "comedy"]}},
    {"title": "Slaughterhouse-Five", "author": "Kurt Vonnegut", "metadata_": {"year": 1969, "genre": ["literary fiction", "absurdist"]}},
    {"title": "Catch-22", "author": "Joseph Heller", "metadata_": {"year": 1961, "genre": ["literary fiction", "absurdist"]}},

    # --- Thriller / Gothic Romance (3) ---
    {"title": "Rebecca", "author": "Daphne du Maurier", "metadata_": {"year": 1938, "genre": ["gothic romance", "thriller"]}},
    {"title": "Gone Girl", "author": "Gillian Flynn", "metadata_": {"year": 2012, "genre": ["thriller", "mystery"]}},
    {"title": "The Secret History", "author": "Donna Tartt", "metadata_": {"year": 1992, "genre": ["literary fiction", "thriller"]}},

    # --- War / Historical (3) ---
    {"title": "All Quiet on the Western Front", "author": "Erich Maria Remarque", "metadata_": {"year": 1929, "genre": ["war fiction", "classic"]}},
    {"title": "The Book Thief", "author": "Markus Zusak", "metadata_": {"year": 2005, "genre": ["historical fiction", "young adult"]}},
    {"title": "The Things They Carried", "author": "Tim O'Brien", "metadata_": {"year": 1990, "genre": ["war fiction", "literary fiction"]}},

    # --- Memoir (2) ---
    {"title": "When Breath Becomes Air", "author": "Paul Kalanithi", "metadata_": {"year": 2016, "genre": ["memoir", "nonfiction"]}},
    {"title": "The Year of Magical Thinking", "author": "Joan Didion", "metadata_": {"year": 2005, "genre": ["memoir", "nonfiction"]}},

    # --- Magical Realism (2) ---
    {"title": "Klara and the Sun", "author": "Kazuo Ishiguro", "metadata_": {"year": 2021, "genre": ["science fiction", "literary fiction"]}},
    {"title": "The House of the Spirits", "author": "Isabel Allende", "metadata_": {"year": 1982, "genre": ["magical realism", "historical"]}},
]


async def seed(run_analysis: bool = False):
    await init_db()

    async with async_session() as session:
        existing = await session.execute(select(Book.title))
        existing_titles = {row[0] for row in existing.fetchall()}

        for book_data in SEED_BOOKS:
            if book_data["title"] in existing_titles:
                logger.info(f"Skipping (exists): {book_data['title']}")
                continue

            book = Book(
                title=book_data["title"],
                author=book_data["author"],
                metadata_=book_data["metadata_"],
                analysis_status="pending",
            )
            session.add(book)
            logger.info(f"Added: {book_data['title']}")

        await session.commit()

    if run_analysis:
        logger.info("Running emotional analysis on all pending books...")
        async with async_session() as session:
            result = await session.execute(
                select(Book).where(Book.analysis_status == "pending")
            )
            pending_books = result.scalars().all()

            for book in pending_books:
                logger.info(f"Analyzing: {book.title}...")
                try:
                    analysis = await analyze_book(book.title, book.author)
                    book.description = analysis["description"]
                    book.emotion_breakdown = analysis["emotion_breakdown"]
                    book.emotion_vector = analysis["emotion_vector"]
                    book.raw_claude_response = analysis["raw_response"]
                    book.analysis_status = "completed"
                    await session.commit()
                    logger.info(f"  Done: {book.title}")
                except Exception as e:
                    logger.error(f"  Failed: {book.title} -- {e}")
                    book.analysis_status = "failed"
                    await session.commit()

    logger.info("Seeding complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze", action="store_true", help="Run emotional analysis on seeded books")
    args = parser.parse_args()
    asyncio.run(seed(run_analysis=args.analyze))
