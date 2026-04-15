"""
Evaluation tests for the recommendation algorithm.

Tests verify that:
1. Rating a single book highly surfaces emotionally similar books
2. Rating 4-5 books highly surfaces an expected 6th book
3. Cross-genre emotional matching works (the core value proposition)
4. Emotionally opposite books do NOT match

Run with: python -m pytest tests/test_recommendations.py -v
"""

import pytest
import pytest_asyncio
import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.models.book import Book
import ssl as _ssl

_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

engine = create_async_engine(
    settings.database_url,
    connect_args={"ssl": _ssl_ctx},
)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def session():
    async with TestSession() as s:
        yield s
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def get_book(s: AsyncSession, title: str) -> Book:
    result = await s.execute(select(Book).where(Book.title == title))
    book = result.scalar_one_or_none()
    assert book is not None, f"Book '{title}' not found"
    assert book.emotion_vector is not None, f"Book '{title}' has no vector"
    return book


async def similar_titles(s: AsyncSession, book: Book, limit: int = 10) -> list[str]:
    vec_str = "[" + ",".join(str(v) for v in book.emotion_vector) + "]"
    rows = (await s.execute(text(
        "SELECT id FROM books "
        "WHERE id != :bid AND emotion_vector IS NOT NULL "
        "ORDER BY emotion_vector <=> CAST(:vec AS vector) LIMIT :lim"
    ), {"vec": vec_str, "bid": str(book.id), "lim": limit})).fetchall()
    titles = []
    for row in rows:
        b = await s.get(Book, row[0])
        titles.append(b.title)
    return titles


async def recommend_titles(
    s: AsyncSession, ratings: list[tuple[str, float]], limit: int = 10
) -> list[str]:
    """Mirrors the preference vector logic from app.routers.recommend."""
    from app.routers.recommend import build_preference_vector

    vectors, rating_vals, rated_ids = [], [], set()
    for title, rating in ratings:
        book = await get_book(s, title)
        vectors.append(np.array(book.emotion_vector, dtype=np.float64))
        rating_vals.append(rating)
        rated_ids.add(str(book.id))

    preference = build_preference_vector(vectors, rating_vals)

    vec_str = "[" + ",".join(str(v) for v in preference.tolist()) + "]"
    placeholders = ", ".join(f"'{rid}'" for rid in rated_ids)
    rows = (await s.execute(text(
        f"SELECT id FROM books "
        f"WHERE id NOT IN ({placeholders}) AND emotion_vector IS NOT NULL "
        f"ORDER BY emotion_vector <=> CAST(:vec AS vector) LIMIT :lim"
    ), {"vec": vec_str, "lim": limit})).fetchall()
    titles = []
    for row in rows:
        b = await s.get(Book, row[0])
        titles.append(b.title)
    return titles


# ===========================================================================
# Test 1: Single book rated high → expected similar books in top 5
# ===========================================================================

SINGLE_BOOK_TESTS = [
    (
        "Rebecca",
        ["The Shining", "The Haunting of Hill House"],
        "Gothic dread + obsession + vulnerability cluster",
    ),
    (
        "Annihilation",
        ["Kafka on the Shore", "Solaris"],
        "Cosmic dread + confusion + alienation cluster",
    ),
    (
        "The Road",
        ["A Little Life", "Frankenstein"],
        "Unrelenting devastation + grief + vulnerability",
    ),
    (
        "No Longer Human",
        ["The Bell Jar"],
        "Alienation + vulnerability + self-destructive despair",
    ),
    (
        "One Hundred Years of Solitude",
        ["The House of the Spirits"],
        "Magical realism + multigenerational wonder + nostalgia",
    ),
    (
        "Beloved",
        ["Frankenstein"],
        "Cross-genre: grief + alienation + moral ambiguity",
    ),
    (
        "The Hobbit",
        ["The Name of the Wind"],
        "Wonder + warmth + adventure in fantasy",
    ),
    (
        "Never Let Me Go",
        ["A Little Life"],
        "Cross-genre: quiet grief + vulnerability + inevitable loss",
    ),
    (
        "The Shining",
        ["The Haunting of Hill House", "Rebecca"],
        "Psychological horror + isolation + dread",
    ),
    (
        "Slaughterhouse-Five",
        ["Kafka on the Shore", "Catch-22"],
        "Absurdist detachment + existential complexity",
    ),
]


@pytest.mark.parametrize("rated,expected,reason", SINGLE_BOOK_TESTS)
@pytest.mark.asyncio
async def test_single_book_similarity(session, rated, expected, reason):
    """Rate one book highly -> expected books appear in top 5."""
    book = await get_book(session, rated)
    top5 = await similar_titles(session, book, limit=5)
    for exp in expected:
        assert exp in top5, (
            f"'{exp}' not in top 5 similar to '{rated}' ({reason}). Got: {top5}"
        )


# ===========================================================================
# Test 2: Multiple books rated high → expect a specific 6th recommendation
# ===========================================================================

MULTI_BOOK_TESTS = [
    (
        [("The Road", 5), ("A Little Life", 5), ("Beloved", 4), ("All Quiet on the Western Front", 4)],
        "Frankenstein",
        "Grief + isolation + moral weight blend",
    ),
    (
        [("Rebecca", 5), ("The Haunting of Hill House", 5), ("Mexican Gothic", 4), ("The Shining", 4)],
        "1984",
        "Dread + claustrophobia + vulnerability — 1984 shares oppressive atmosphere",
    ),
    (
        [("Annihilation", 5), ("Solaris", 5), ("House of Leaves", 4)],
        "Kafka on the Shore",
        "Confusion + dread + wonder — Kafka matches surreal unease",
    ),
    (
        [("Flowers for Algernon", 5), ("Never Let Me Go", 5), ("The Book Thief", 4), ("When Breath Becomes Air", 4)],
        "Normal People",
        "Gentle grief + vulnerability + intimacy",
    ),
    (
        [("One Hundred Years of Solitude", 5), ("The House of the Spirits", 5), ("The God of Small Things", 4)],
        "The Great Gatsby",
        "Multigenerational weight + nostalgia + sensuality",
    ),
    (
        [("Norwegian Wood", 5), ("Normal People", 5), ("Never Let Me Go", 4)],
        "Flowers for Algernon",
        "Intimate melancholy + longing + quiet vulnerability",
    ),
    (
        [("The Hobbit", 5), ("The Name of the Wind", 5), ("Piranesi", 4), ("A Wizard of Earthsea", 4)],
        "Circe",
        "Wonder + warmth + contemplation in fantasy",
    ),
    (
        [("1984", 5), ("The Handmaid's Tale", 5), ("Fahrenheit 451", 4)],
        "Rebecca",
        "Dread + claustrophobia + vulnerability — oppressive atmosphere cluster",
    ),
]


@pytest.mark.parametrize("ratings,expected,reason", MULTI_BOOK_TESTS)
@pytest.mark.asyncio
async def test_multi_book_recommendation(session, ratings, expected, reason):
    """Rate 4-5 books highly -> expected book appears in top 5 recommendations."""
    top5 = await recommend_titles(session, ratings, limit=5)
    assert expected in top5, (
        f"'{expected}' not in top 5 recs ({reason}). Got: {top5}"
    )


# ===========================================================================
# Test 3: Cross-genre matching (core value proposition)
# ===========================================================================

CROSS_GENRE_TESTS = [
    ("Beloved", "Frankenstein", "literary fiction / gothic sci-fi",
     "Deep grief + alienation + moral ambiguity"),
    ("Never Let Me Go", "Flowers for Algernon", "literary sci-fi / sci-fi",
     "Quiet inevitable grief + vulnerability"),
    ("The Road", "A Little Life", "post-apocalyptic / contemporary",
     "Devastating isolation + grief + vulnerability"),
    ("Solaris", "House of Leaves", "philosophical sci-fi / experimental horror",
     "Isolation + confusion + cosmic dread + disorientation"),
]


@pytest.mark.parametrize("book_a,book_b,genres,reason", CROSS_GENRE_TESTS)
@pytest.mark.asyncio
async def test_cross_genre_similarity(session, book_a, book_b, genres, reason):
    """Books from different genres should appear in each other's top 10."""
    a = await get_book(session, book_a)
    top10 = await similar_titles(session, a, limit=10)
    assert book_b in top10, (
        f"Cross-genre: '{book_b}' not in top 10 for '{book_a}' ({genres}). "
        f"{reason}. Got: {top10}"
    )


# ===========================================================================
# Test 4: Dissimilar books should NOT match
# ===========================================================================

DISSIMILAR_TESTS = [
    ("The Hitchhiker's Guide to the Galaxy", "A Little Life",
     "Absurdist comedy vs devastating emotional trauma"),
    ("The House in the Cerulean Sea", "Blood Meridian",
     "Cozy warmth vs nihilistic violence"),
    ("Piranesi", "Gone Girl",
     "Serene wonder vs frenetic psychological tension"),
    ("The Hobbit", "No Longer Human",
     "Warm adventure vs alienated despair"),
]


@pytest.mark.parametrize("book_a,book_b,reason", DISSIMILAR_TESTS)
@pytest.mark.asyncio
async def test_dissimilar_not_close(session, book_a, book_b, reason):
    """Emotionally opposite books should NOT appear in each other's top 5."""
    a = await get_book(session, book_a)
    top5 = await similar_titles(session, a, limit=5)
    assert book_b not in top5, (
        f"'{book_b}' should NOT be in top 5 for '{book_a}'. {reason}. Got: {top5}"
    )


# ===========================================================================
# Test 5: Low ratings push recommendations AWAY from those emotions
# ===========================================================================

# When a user rates a book 1 star, they dislike its emotional profile.
# Recommendations should avoid books with similar emotions.

LOW_RATING_AVOIDANCE_TESTS = [
    # (high-rated books, low-rated book, should NOT appear in top 5, reason)
    (
        [("Piranesi", 5), ("The Hobbit", 5)],
        ("The Road", 1),
        ["A Little Life", "All Quiet on the Western Front"],
        "Loves wonder/warmth, hates dread/grief — should avoid devastation",
    ),
    (
        [("The House in the Cerulean Sea", 5), ("The Hobbit", 5)],
        ("House of Leaves", 1),
        ["The Shining", "Annihilation"],
        "Loves cozy warmth, hates horror/confusion — should avoid dread",
    ),
    (
        [("Project Hail Mary", 5), ("Piranesi", 5)],
        ("No Longer Human", 1),
        ["The Bell Jar", "A Little Life"],
        "Loves wonder/empowerment, hates alienation/despair — should avoid vulnerability",
    ),
    (
        [("The Name of the Wind", 5), ("Circe", 5)],
        ("1984", 1),
        ["The Handmaid's Tale", "The Shining"],
        "Loves fantasy warmth, hates oppressive dystopia — should avoid claustrophobia",
    ),
]


@pytest.mark.parametrize("liked,disliked,should_not_appear,reason", LOW_RATING_AVOIDANCE_TESTS)
@pytest.mark.asyncio
async def test_low_rating_pushes_away(session, liked, disliked, should_not_appear, reason):
    """Rating a book 1 star should push recommendations away from its emotions."""
    all_ratings = liked + [disliked]
    top5 = await recommend_titles(session, all_ratings, limit=5)
    for avoid in should_not_appear:
        assert avoid not in top5, (
            f"'{avoid}' should NOT appear when user dislikes '{disliked[0]}'. "
            f"{reason}. Got: {top5}"
        )


# ===========================================================================
# Test 6: Low rating shifts results compared to without it
# ===========================================================================

# Adding a 1-star rating should meaningfully change the recommendations
# compared to only having the high ratings.

SHIFT_TESTS = [
    # (high-rated books, low-rated book to add, a book that should be displaced, reason)
    (
        [("Rebecca", 5), ("The Haunting of Hill House", 5)],
        ("The Hitchhiker's Guide to the Galaxy", 1),
        "The Hitchhiker's Guide to the Galaxy",
        "Disliking absurdist comedy should not pull recs toward it",
    ),
    (
        [("Flowers for Algernon", 5), ("Never Let Me Go", 5)],
        ("Blood Meridian", 1),
        "Blood Meridian",
        "Disliking nihilistic violence should not pull recs toward it",
    ),
]


@pytest.mark.parametrize("liked,disliked,excluded_book,reason", SHIFT_TESTS)
@pytest.mark.asyncio
async def test_low_rating_shifts_results(session, liked, disliked, excluded_book, reason):
    """Adding a 1-star rating should change recommendations vs only high ratings."""
    # Get recs with only high ratings
    top10_without = await recommend_titles(session, liked, limit=10)

    # Get recs with the low rating added
    all_ratings = liked + [disliked]
    top10_with = await recommend_titles(session, all_ratings, limit=10)

    # The results should differ
    assert top10_without != top10_with, (
        f"Adding 1-star '{disliked[0]}' should change recommendations. "
        f"{reason}. Both returned: {top10_without}"
    )


# ===========================================================================
# Test 7: Mixed ratings create a coherent emotional preference
# ===========================================================================

MIXED_RATING_TESTS = [
    (
        [
            ("The Road", 1),           # hates: dread, isolation, grief
            ("A Little Life", 1),      # hates: grief, vulnerability, dread
            ("The House in the Cerulean Sea", 5),  # loves: warmth, joy, comfort
            ("The Hobbit", 5),         # loves: wonder, warmth, joy
            ("Piranesi", 5),           # loves: wonder, serenity, isolation
        ],
        ["The Name of the Wind", "Circe", "Klara and the Sun"],
        ["Blood Meridian", "House of Leaves", "No Longer Human"],
        "Loves warmth+wonder, hates dread+grief — should get warm books, not dark ones",
    ),
    (
        [
            ("The Hitchhiker's Guide to the Galaxy", 1),  # hates: absurdity, joy
            ("The House in the Cerulean Sea", 1),          # hates: warmth, comfort
            ("The Road", 5),           # loves: dread, isolation, grief
            ("House of Leaves", 5),    # loves: dread, confusion, obsession
            ("1984", 5),               # loves: dread, claustrophobia, anger
        ],
        ["Beloved", "Frankenstein", "Dune"],
        ["The Hobbit", "Piranesi", "The Name of the Wind"],
        "Loves dread+darkness, hates warmth+levity — should get dark books, not cozy ones",
    ),
    (
        [
            ("Blood Meridian", 1),     # hates: dread, chaos, violence
            ("Gone Girl", 1),          # hates: tension, anger, moral ambiguity
            ("Norwegian Wood", 5),     # loves: melancholy, nostalgia, intimacy
            ("Normal People", 5),      # loves: intimacy, vulnerability, melancholy
            ("Never Let Me Go", 5),    # loves: melancholy, grief, vulnerability
        ],
        ["Flowers for Algernon", "The God of Small Things"],
        ["The Shining", "House of Leaves", "Annihilation"],
        "Loves quiet intimacy, hates violent tension — should get gentle emotional books",
    ),
]


@pytest.mark.parametrize("ratings,should_appear,should_not_appear,reason", MIXED_RATING_TESTS)
@pytest.mark.asyncio
async def test_mixed_ratings_preference(session, ratings, should_appear, should_not_appear, reason):
    """Mixed high/low ratings should create a coherent preference that surfaces matching books."""
    top10 = await recommend_titles(session, ratings, limit=10)

    # At least one of the expected books should appear in top 10
    found = [b for b in should_appear if b in top10]
    assert len(found) > 0, (
        f"None of {should_appear} found in top 10. {reason}. Got: {top10}"
    )

    # None of the avoided books should appear in top 5
    top5 = top10[:5]
    for avoid in should_not_appear:
        assert avoid not in top5, (
            f"'{avoid}' should NOT be in top 5. {reason}. Got: {top5}"
        )
