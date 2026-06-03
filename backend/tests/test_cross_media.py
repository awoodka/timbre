"""Cross-media validation — the core Timbre thesis.

Does a film land near its source novel in the SHARED emotional space, rather than
clustering with other films by medium? Requires both books and films seeded.
Uses `media_corpus` keyed by (medium, title) since a novel and its film share a title.
"""

import numpy as np
import pytest

from tests._helpers import cosine

# Titles present as BOTH a seeded book and a seeded film (identical title).
NOVEL_FILM_PAIRS = [
    "The Road", "Annihilation", "The Shining", "Solaris", "Gone Girl",
    "Never Let Me Go", "Dune", "Rebecca", "The Great Gatsby", "The Book Thief",
]

# (title, emotionally-opposite book) — the film should sit nearer its own novel.
OPPOSITE_TRIPLETS = [
    ("The Road", "The Hobbit"),
    ("Annihilation", "The House in the Cerulean Sea"),
    ("The Shining", "The Hobbit"),
    ("Solaris", "The House in the Cerulean Sea"),
    ("Gone Girl", "The Hobbit"),
    ("Never Let Me Go", "The House in the Cerulean Sea"),
]


@pytest.mark.parametrize("title,opposite", OPPOSITE_TRIPLETS)
def test_film_nearer_its_novel_than_an_opposite_book(media_corpus, title, opposite):
    for key in [("film", title), ("book", title), ("book", opposite)]:
        if key not in media_corpus:
            pytest.skip(f"{key} not seeded/analyzed")
    film = media_corpus[("film", title)]["vec"]
    s_src = cosine(film, media_corpus[("book", title)]["vec"])
    s_opp = cosine(film, media_corpus[("book", opposite)]["vec"])
    assert s_src > s_opp, (
        f"'{title}' film is closer to the opposite book '{opposite}' ({s_opp:.3f}) "
        f"than to its own novel ({s_src:.3f}) — cross-media emotion not aligning."
    )


def test_adaptations_sit_near_their_source(media_corpus):
    """On average, a film is more similar to its source novel than to a random book."""
    books = {t: v for (m, t), v in media_corpus.items() if m == "book"}
    pairs = [t for t in NOVEL_FILM_PAIRS
             if ("film", t) in media_corpus and ("book", t) in media_corpus]
    if len(pairs) < 3:
        pytest.skip("need >= 3 novel/film pairs seeded")
    src, rand = [], []
    for t in pairs:
        film = media_corpus[("film", t)]["vec"]
        src.append(cosine(film, books[t]["vec"]))
        rand += [cosine(film, v["vec"]) for bt, v in books.items() if bt != t]
    assert np.mean(src) > np.mean(rand), (
        f"Adaptations not nearer their source: mean(source)={np.mean(src):.3f} "
        f"vs mean(random book)={np.mean(rand):.3f}"
    )


def test_media_share_one_space_not_disjoint_clusters(media_corpus):
    """Films and books must not split into medium-separated clusters — strong
    cross-media matches must exist (guards the medium-dominates failure mode)."""
    films = [v["vec"] for (m, t), v in media_corpus.items() if m == "film"]
    books = [v["vec"] for (m, t), v in media_corpus.items() if m == "book"]
    if not films or not books:
        pytest.skip("need both media seeded")
    best_cross = max(cosine(f, b) for f in films for b in books)
    assert best_cross > 0.4, (
        f"No strong cross-media similarity (max film<->book cosine={best_cross:.3f}); "
        "media may be separated into per-medium clusters."
    )
