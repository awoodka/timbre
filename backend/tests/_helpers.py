"""Source-grounded ground truth + similarity helpers for the embedding test suite.

WHAT THESE TESTS MEASURE
Timbre's claim is that the 31-dim space captures *emotional* kinship — mood and
arc — rather than genre/plot. So the ground truth below is organized by felt
experience, deliberately crossing genre lines, and the tests assert RELATIVE
structure (A is closer to B than to C) rather than brittle absolute top-k
membership.

GROUND-TRUTH SOURCING (retrieved 2026-06; corroborating broad critical/reader consensus)
- Bleak/devastating endings: shortlist.com "30 Saddest Endings in Literature",
  bookriot.com "books-with-sad-endings", bustle.com sad-endings
  (explicitly incl. Flowers for Algernon).
- Uplifting/hopeful endings: bookriot.com "books-with-happy-endings",
  brokebybooks.com "15-best-books-with-happy-endings".
- Cozy/comfort (warm, low-stakes): scarymommy.com comforting-books,
  icpl.org cozy-fantasy (Legends & Lattes lineage -> Cerulean Sea / Hobbit).
- Cosmic/atmospheric dread: goodreads.com/list/show/138996 "Cosmic Horror"
  (groups Annihilation + House of Leaves).
- Quiet melancholy/longing: harpercollins.co.uk "books-like-norwegian-wood",
  starbookmark.com (groups No Longer Human + Never Let Me Go with Norwegian Wood).

Only titles present in the seeded corpus are referenced.
"""

import numpy as np

# --- Emotional-kinship clusters (mood-based, cross-genre) -------------------
CLUSTERS = {
    # Unrelenting devastation / grief / bleakness.
    "devastation": [
        "A Little Life", "The Road", "Blood Meridian", "No Longer Human",
        "All Quiet on the Western Front", "The Things They Carried",
    ],
    # Warm, hopeful, low-stakes / earned uplift.
    "cozy_uplifting": [
        "The House in the Cerulean Sea", "The Hobbit", "Project Hail Mary",
        "The Hitchhiker's Guide to the Galaxy",
    ],
    # Atmospheric / cosmic / psychological dread.
    "cosmic_dread": [
        "Annihilation", "House of Leaves", "Solaris",
        "The Haunting of Hill House", "Mexican Gothic", "The Shining",
    ],
    # Quiet melancholy, longing, alienation.
    "melancholy_longing": [
        "Norwegian Wood", "Never Let Me Go", "No Longer Human",
        "Kafka on the Shore", "Klara and the Sun", "Normal People",
    ],
    # Oppressive dystopia.
    "oppressive_dystopia": [
        "1984", "The Handmaid's Tale", "Fahrenheit 451", "Brave New World",
    ],
}

# --- Ending / arc valence (sourced; see module docstring) -------------------
# Bleak, tragic, devastating finishes -> ending_valence should be LOW.
ARC_TRAGIC = [
    "A Little Life", "1984", "No Longer Human", "Blood Meridian", "The Road",
    "Never Let Me Go", "Gone Girl", "Brave New World",
    "The Year of Magical Thinking", "The God of Small Things",
    "Flowers for Algernon",
]
# Uplifting, redemptive, triumphant finishes -> ending_valence should be HIGH.
ARC_UPLIFTING = [
    "The House in the Cerulean Sea", "The Hobbit", "Project Hail Mary",
    "The Hitchhiker's Guide to the Galaxy", "A Wizard of Earthsea", "Circe",
]

# --- Per-book consensus dominant / absent emotions --------------------------
# (title, dimension, k): `dimension` must be among the book's top-k scores.
EXPECTED_DOMINANT = [
    ("The Road", "dread", 3),
    ("A Little Life", "grief", 3),
    ("Blood Meridian", "dread", 3),
    ("The House in the Cerulean Sea", "warmth", 3),
    ("The Hobbit", "wonder", 5),
    ("Norwegian Wood", "melancholy", 3),
    ("1984", "dread", 5),
    ("Annihilation", "dread", 5),
    ("Beloved", "grief", 5),
    ("The Shining", "dread", 5),
    ("No Longer Human", "alienation", 5),
]
# (title, dimension, k): `dimension` must NOT be among the top-k (inflation guard).
EXPECTED_ABSENT = [
    ("The House in the Cerulean Sea", "dread", 6),
    ("The Hobbit", "dread", 5),
    ("The Hitchhiker's Guide to the Galaxy", "grief", 6),
]

# ===========================================================================
# FILM ground truth (sourced; mirrors the book ground truth above)
# ===========================================================================
# Sourcing (retrieved 2026-06): collider.com (most-emotional, soul-crushing,
# cosmic-horror, best/bleakest/feel-good movie endings), tasteofcinema
# (atmospheric), rottentomatoes (feel-good). Mood/arc groupings deliberately
# cross genre — the property the shared cross-media space must capture.
FILM_CLUSTERS = {
    "devastation": [
        "Schindler's List", "Grave of the Fireflies", "Come and See",
        "Manchester by the Sea", "Requiem for a Dream", "The Road",
        "12 Years a Slave", "Amour",
    ],
    "cozy_uplifting": [
        "My Neighbor Totoro", "Paddington 2", "Amélie", "Up",
        "The Shawshank Redemption", "Little Women", "Spirited Away",
    ],
    "horror_dread": [
        "The Thing", "Alien", "The Lighthouse", "Hereditary", "The Shining",
    ],
    "melancholy_longing": [
        "Lost in Translation", "In the Mood for Love", "Her", "Past Lives",
        "Moonlight", "Call Me by Your Name", "Cinema Paradiso",
    ],
    "tension_thriller": [
        "No Country for Old Men", "Parasite", "Se7en", "Prisoners", "Gone Girl",
    ],
    "awe_scifi": [
        "2001: A Space Odyssey", "Arrival", "Interstellar", "Annihilation",
    ],
}

FILM_ARC_TRAGIC = [
    "Grave of the Fireflies", "Come and See", "Requiem for a Dream", "Amour",
    "Se7en", "Hereditary", "The Lighthouse", "Nineteen Eighty-Four",
    "No Country for Old Men", "Prisoners", "The Shining", "Brazil", "Gone Girl",
    "The Road", "Manchester by the Sea",
]
FILM_ARC_UPLIFTING = [
    "The Shawshank Redemption", "Paddington 2", "Amélie", "My Neighbor Totoro",
    "Up", "Spirited Away", "Little Women",
]

FILM_EXPECTED_DOMINANT = [
    ("The Thing", "dread", 3),
    ("Grave of the Fireflies", "grief", 3),
    ("Hereditary", "dread", 3),
    ("My Neighbor Totoro", "warmth", 4),
    ("Paddington 2", "warmth", 3),
    ("Lost in Translation", "melancholy", 3),
    ("2001: A Space Odyssey", "wonder", 3),
    ("Parasite", "tension", 4),
    ("Manchester by the Sea", "grief", 3),
    ("The Lighthouse", "dread", 3),
    ("In the Mood for Love", "melancholy", 3),
    ("Her", "melancholy", 4),
    ("Se7en", "dread", 3),
    ("Interstellar", "wonder", 5),
    ("Schindler's List", "grief", 5),
]
FILM_EXPECTED_ABSENT = [
    ("My Neighbor Totoro", "dread", 6),
    ("Paddington 2", "dread", 6),
    ("Amélie", "dread", 6),
]


# --- similarity helpers (operate on a `corpus` fixture — books OR films) -----
def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0


def sim(corpus: dict, t1: str, t2: str) -> float:
    return cosine(corpus[t1]["vec"], corpus[t2]["vec"])


def present(corpus: dict, titles) -> list:
    """Filter a title list to those actually in the corpus (defensive)."""
    return [t for t in titles if t in corpus]


def nearest(corpus: dict, title: str, k: int = 5) -> list:
    others = [(sim(corpus, title, t), t) for t in corpus if t != title]
    return [t for _, t in sorted(others, reverse=True)[:k]]


def top_dims(corpus: dict, title: str, k: int) -> list:
    scores = corpus[title]["scores"]
    return [d for d, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:k]]


def score_of(corpus: dict, title: str, dim: str) -> float:
    return corpus[title]["scores"][dim]


def mean_within_sim(corpus: dict, group) -> float:
    g = present(corpus, group)
    pairs = [sim(corpus, a, b) for i, a in enumerate(g) for b in g[i + 1:]]
    return float(np.mean(pairs)) if pairs else 0.0


def mean_cross_sim(corpus: dict, group_a, group_b) -> float:
    ga, gb = present(corpus, group_a), present(corpus, group_b)
    pairs = [sim(corpus, a, b) for a in ga for b in gb if a != b]
    return float(np.mean(pairs)) if pairs else 0.0


def preference_recommend(corpus: dict, ratings, k: int = 10) -> list:
    """Replicate the /recommend ranking against the loaded corpus.

    `ratings` is a list of (title, rating). Uses the production
    build_preference_vector so tests exercise the real preference logic.
    """
    from app.routers.recommend import build_preference_vector

    vecs = [corpus[t]["vec"] for t, _ in ratings]
    pref = build_preference_vector(vecs, [r for _, r in ratings])
    rated = {t for t, _ in ratings}
    ranked = sorted(
        ((cosine(pref, corpus[t]["vec"]), t) for t in corpus if t not in rated),
        reverse=True,
    )
    return [t for _, t in ranked[:k]]
