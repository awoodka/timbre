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


# Shows that are also seeded books (identical title), + an emotionally-opposite book.
SHOW_OPPOSITE_TRIPLETS = [
    ("The Haunting of Hill House", "The Hobbit"),
    ("The Handmaid's Tale", "The Hobbit"),
    ("Normal People", "Blood Meridian"),
]


@pytest.mark.parametrize("title,opposite", SHOW_OPPOSITE_TRIPLETS)
def test_show_nearer_its_novel_than_an_opposite_book(media_corpus, title, opposite):
    for key in [("show", title), ("book", title), ("book", opposite)]:
        if key not in media_corpus:
            pytest.skip(f"{key} not seeded/analyzed")
    show = media_corpus[("show", title)]["vec"]
    s_src = cosine(show, media_corpus[("book", title)]["vec"])
    s_opp = cosine(show, media_corpus[("book", opposite)]["vec"])
    assert s_src > s_opp, (
        f"'{title}' show is closer to the opposite book '{opposite}' ({s_opp:.3f}) "
        f"than to its own novel ({s_src:.3f})."
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


# Works seeded as BOTH anime and manga (shared title) → manga↔anime pairs.
MANGA_ANIME_PAIRS = [
    "Berserk", "Attack on Titan", "Death Note", "Monster", "Vinland Saga",
    "Tokyo Ghoul", "Chainsaw Man", "Demon Slayer", "Jujutsu Kaisen",
    "Hunter x Hunter", "Spy x Family",
]

# (title, emotionally-opposite work-of-the-other-medium)
ANIME_MANGA_OPPOSITE = [
    ("Berserk", ("manga", "Yotsuba&!")),
    ("Attack on Titan", ("manga", "Yotsuba&!")),
    ("Death Note", ("manga", "Yotsuba&!")),
    ("Monster", ("manga", "Yotsuba&!")),
    ("Spy x Family", ("manga", "Berserk")),
]


@pytest.mark.parametrize("title,opposite", ANIME_MANGA_OPPOSITE)
def test_anime_nearer_its_manga_than_opposite(media_corpus, title, opposite):
    if ("anime", title) not in media_corpus or ("manga", title) not in media_corpus or opposite not in media_corpus:
        pytest.skip(f"{title} pair or opposite not seeded")
    a = media_corpus[("anime", title)]["vec"]
    own = cosine(a, media_corpus[("manga", title)]["vec"])
    opp = cosine(a, media_corpus[opposite]["vec"])
    assert own > opp, (
        f"'{title}' anime closer to {opposite} ({opp:.3f}) than to its own manga ({own:.3f})."
    )


def test_anime_manga_adaptations_align(media_corpus):
    """A work's anime should, on average, be nearer its own manga than a random manga."""
    mangas = {t: v for (m, t), v in media_corpus.items() if m == "manga"}
    pairs = [t for t in MANGA_ANIME_PAIRS if ("anime", t) in media_corpus and t in mangas]
    if len(pairs) < 3:
        pytest.skip("need >= 3 anime/manga pairs")
    own, rand = [], []
    for t in pairs:
        a = media_corpus[("anime", t)]["vec"]
        own.append(cosine(a, mangas[t]["vec"]))
        rand += [cosine(a, v["vec"]) for mt, v in mangas.items() if mt != t]
    assert np.mean(own) > np.mean(rand), (
        f"anime/manga adaptations not aligned: own={np.mean(own):.3f} vs random={np.mean(rand):.3f}"
    )


# Games have few same-title cross-media pairs, so validate via emotional ANALOGUES:
# (game, emotionally-similar work of another medium, emotionally-opposite work).
GAME_ANALOGUE_TRIPLETS = [
    ("The Last of Us", ("film", "The Road"), ("book", "The Hobbit")),
    ("Silent Hill 2", ("film", "The Shining"), ("book", "The Hobbit")),
    ("Disco Elysium", ("book", "No Longer Human"), ("anime", "K-On!")),
    ("Outer Wilds", ("film", "Arrival"), ("book", "The Hobbit")),
    ("Stardew Valley", ("show", "Ted Lasso"), ("book", "Blood Meridian")),
    ("Cyberpunk 2077", ("book", "Neuromancer"), ("anime", "K-On!")),
]


@pytest.mark.parametrize("game,analogue,opposite", GAME_ANALOGUE_TRIPLETS)
def test_game_nearer_its_analogue_than_opposite(media_corpus, game, analogue, opposite):
    g = ("game", game)
    for key in (g, analogue, opposite):
        if key not in media_corpus:
            pytest.skip(f"{key} not seeded")
    gv = media_corpus[g]["vec"]
    s_an = cosine(gv, media_corpus[analogue]["vec"])
    s_op = cosine(gv, media_corpus[opposite]["vec"])
    assert s_an > s_op, (
        f"'{game}' closer to opposite {opposite} ({s_op:.3f}) than its analogue {analogue} ({s_an:.3f})."
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
