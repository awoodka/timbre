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
from app.models.media import MediaItem
from app.services.emotional_analysis import analyze_media
from app.services.embeddings import recompute_all_embeddings
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


SEED_FILMS = [
    # --- Devastation / grief / war ---
    {"title": "Schindler's List", "director": "Steven Spielberg", "metadata_": {"year": 1993, "genre": ["war", "historical", "drama"]}},
    {"title": "Grave of the Fireflies", "director": "Isao Takahata", "metadata_": {"year": 1988, "genre": ["animation", "war", "drama"]}},
    {"title": "Come and See", "director": "Elem Klimov", "metadata_": {"year": 1985, "genre": ["war", "drama"]}},
    {"title": "Manchester by the Sea", "director": "Kenneth Lonergan", "metadata_": {"year": 2016, "genre": ["drama"]}},
    {"title": "Requiem for a Dream", "director": "Darren Aronofsky", "metadata_": {"year": 2000, "genre": ["drama", "psychological"]}},
    {"title": "The Road", "director": "John Hillcoat", "metadata_": {"year": 2009, "genre": ["post-apocalyptic", "drama"]}},
    {"title": "12 Years a Slave", "director": "Steve McQueen", "metadata_": {"year": 2013, "genre": ["historical", "drama"]}},
    {"title": "Amour", "director": "Michael Haneke", "metadata_": {"year": 2012, "genre": ["drama", "romance"]}},

    # --- Cosmic / atmospheric / horror ---
    {"title": "The Thing", "director": "John Carpenter", "metadata_": {"year": 1982, "genre": ["horror", "science fiction"]}},
    {"title": "Annihilation", "director": "Alex Garland", "metadata_": {"year": 2018, "genre": ["science fiction", "horror"]}},
    {"title": "The Lighthouse", "director": "Robert Eggers", "metadata_": {"year": 2019, "genre": ["horror", "psychological"]}},
    {"title": "Hereditary", "director": "Ari Aster", "metadata_": {"year": 2018, "genre": ["horror"]}},
    {"title": "Stalker", "director": "Andrei Tarkovsky", "metadata_": {"year": 1979, "genre": ["science fiction", "drama"]}},
    {"title": "Solaris", "director": "Andrei Tarkovsky", "metadata_": {"year": 1972, "genre": ["science fiction", "drama"]}},
    {"title": "The Shining", "director": "Stanley Kubrick", "metadata_": {"year": 1980, "genre": ["horror", "psychological"]}},
    {"title": "Alien", "director": "Ridley Scott", "metadata_": {"year": 1979, "genre": ["science fiction", "horror"]}},

    # --- Dystopia / oppressive ---
    {"title": "Blade Runner", "director": "Ridley Scott", "metadata_": {"year": 1982, "genre": ["science fiction", "cyberpunk"]}},
    {"title": "Children of Men", "director": "Alfonso Cuarón", "metadata_": {"year": 2006, "genre": ["science fiction", "dystopian"]}},
    {"title": "Nineteen Eighty-Four", "director": "Michael Radford", "metadata_": {"year": 1984, "genre": ["science fiction", "dystopian"]}},
    {"title": "Brazil", "director": "Terry Gilliam", "metadata_": {"year": 1985, "genre": ["science fiction", "dystopian"]}},

    # --- Melancholy / longing ---
    {"title": "Lost in Translation", "director": "Sofia Coppola", "metadata_": {"year": 2003, "genre": ["drama", "romance"]}},
    {"title": "In the Mood for Love", "director": "Wong Kar-wai", "metadata_": {"year": 2000, "genre": ["drama", "romance"]}},
    {"title": "Her", "director": "Spike Jonze", "metadata_": {"year": 2013, "genre": ["science fiction", "romance"]}},
    {"title": "Eternal Sunshine of the Spotless Mind", "director": "Michel Gondry", "metadata_": {"year": 2004, "genre": ["science fiction", "romance"]}},
    {"title": "Moonlight", "director": "Barry Jenkins", "metadata_": {"year": 2016, "genre": ["drama"]}},
    {"title": "Past Lives", "director": "Celine Song", "metadata_": {"year": 2023, "genre": ["drama", "romance"]}},
    {"title": "Call Me by Your Name", "director": "Luca Guadagnino", "metadata_": {"year": 2017, "genre": ["drama", "romance"]}},

    # --- Cozy / warm / wonder / uplift ---
    {"title": "My Neighbor Totoro", "director": "Hayao Miyazaki", "metadata_": {"year": 1988, "genre": ["animation", "fantasy", "family"]}},
    {"title": "Spirited Away", "director": "Hayao Miyazaki", "metadata_": {"year": 2001, "genre": ["animation", "fantasy"]}},
    {"title": "The Grand Budapest Hotel", "director": "Wes Anderson", "metadata_": {"year": 2014, "genre": ["comedy", "drama"]}},
    {"title": "Amélie", "director": "Jean-Pierre Jeunet", "metadata_": {"year": 2001, "genre": ["comedy", "romance"]}},
    {"title": "Paddington 2", "director": "Paul King", "metadata_": {"year": 2017, "genre": ["family", "comedy"]}},
    {"title": "Up", "director": "Pete Docter", "metadata_": {"year": 2009, "genre": ["animation", "adventure", "family"]}},
    {"title": "Little Women", "director": "Greta Gerwig", "metadata_": {"year": 2019, "genre": ["drama", "romance"]}},
    {"title": "Cinema Paradiso", "director": "Giuseppe Tornatore", "metadata_": {"year": 1988, "genre": ["drama", "romance"]}},
    {"title": "The Shawshank Redemption", "director": "Frank Darabont", "metadata_": {"year": 1994, "genre": ["drama"]}},

    # --- Tension / thriller ---
    {"title": "No Country for Old Men", "director": "Joel Coen", "metadata_": {"year": 2007, "genre": ["thriller", "crime"]}},
    {"title": "Parasite", "director": "Bong Joon-ho", "metadata_": {"year": 2019, "genre": ["thriller", "drama"]}},
    {"title": "Se7en", "director": "David Fincher", "metadata_": {"year": 1995, "genre": ["thriller", "crime"]}},
    {"title": "Prisoners", "director": "Denis Villeneuve", "metadata_": {"year": 2013, "genre": ["thriller", "crime"]}},
    {"title": "Gone Girl", "director": "David Fincher", "metadata_": {"year": 2014, "genre": ["thriller", "mystery"]}},
    {"title": "Whiplash", "director": "Damien Chazelle", "metadata_": {"year": 2014, "genre": ["drama", "music"]}},

    # --- Awe / sci-fi sublime ---
    {"title": "2001: A Space Odyssey", "director": "Stanley Kubrick", "metadata_": {"year": 1968, "genre": ["science fiction"]}},
    {"title": "Arrival", "director": "Denis Villeneuve", "metadata_": {"year": 2016, "genre": ["science fiction", "drama"]}},
    {"title": "Interstellar", "director": "Christopher Nolan", "metadata_": {"year": 2014, "genre": ["science fiction", "adventure"]}},
    {"title": "Dune", "director": "Denis Villeneuve", "metadata_": {"year": 2021, "genre": ["science fiction", "adventure"]}},

    # --- More novel<->film overlaps ---
    {"title": "Rebecca", "director": "Alfred Hitchcock", "metadata_": {"year": 1940, "genre": ["thriller", "gothic", "drama"]}},
    {"title": "The Great Gatsby", "director": "Baz Luhrmann", "metadata_": {"year": 2013, "genre": ["drama", "romance"]}},
    {"title": "The Book Thief", "director": "Brian Percival", "metadata_": {"year": 2013, "genre": ["war", "drama"]}},
    {"title": "Never Let Me Go", "director": "Mark Romanek", "metadata_": {"year": 2010, "genre": ["science fiction", "drama"]}},
]


async def seed(run_analysis: bool = False):
    await init_db()

    async with async_session() as session:
        existing = await session.execute(select(MediaItem.medium, MediaItem.title))
        existing_keys = {(row[0], row[1]) for row in existing.fetchall()}

        # (medium, title, creator, metadata_) — dedup by (medium, title) so a
        # film adaptation isn't skipped because the namesake book exists.
        to_seed = [
            ("book", b["title"], b["author"], b["metadata_"]) for b in SEED_BOOKS
        ] + [
            ("film", f["title"], f["director"], f["metadata_"]) for f in SEED_FILMS
        ]

        for medium, title, creator, meta in to_seed:
            if (medium, title) in existing_keys:
                logger.info(f"Skipping (exists): [{medium}] {title}")
                continue
            session.add(MediaItem(
                medium=medium,
                title=title,
                creator=creator,
                metadata_=meta,
                analysis_status="pending",
            ))
            logger.info(f"Added: [{medium}] {title}")

        await session.commit()

    if run_analysis:
        logger.info("Running emotional analysis on all pending items...")
        async with async_session() as session:
            result = await session.execute(
                select(MediaItem).where(MediaItem.analysis_status == "pending")
            )
            pending = result.scalars().all()

            for item in pending:
                logger.info(f"Analyzing: {item.title}...")
                try:
                    analysis = await analyze_media(item.medium, item.title, item.creator)
                    item.description = analysis["description"]
                    item.emotion_breakdown = analysis["emotion_breakdown"]
                    item.emotion_vector = analysis["emotion_vector"]
                    item.raw_response = analysis["raw_response"]
                    if analysis.get("cover_image_url"):
                        item.cover_image_url = analysis["cover_image_url"]
                    item.analysis_status = "completed"
                    await session.commit()
                    logger.info(f"  Done: {item.title}")
                except Exception as e:
                    logger.error(f"  Failed: {item.title} -- {e}")
                    item.analysis_status = "failed"
                    await session.commit()

                # Small spacing to stay under LLM / scrape rate limits.
                await asyncio.sleep(1.0)

            # Standardize all vectors against the corpus centroid.
            await recompute_all_embeddings(session)

    logger.info("Seeding complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze", action="store_true", help="Run emotional analysis on seeded books")
    args = parser.parse_args()
    asyncio.run(seed(run_analysis=args.analyze))
