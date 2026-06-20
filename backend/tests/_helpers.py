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


# ===========================================================================
# TV SHOW ground truth (sourced; mirrors the book/film ground truth above)
# ===========================================================================
# Sourcing (retrieved 2026-06): collider.com (greatest TV dramas, sci-fi-horror
# shows), netflix/marieclaire (comfort TV). Series-level emotional signature;
# endings are fuzzier for series, so SHOW_ARC_* keeps to clearly-agreed cases.
SHOW_CLUSTERS = {
    "devastation": [
        "The Leftovers", "Band of Brothers", "Chernobyl", "Six Feet Under",
        "When They See Us",
    ],  # This Is Us excluded — a warm tearjerker, not bleak devastation
    "cozy_uplifting": [
        "Ted Lasso", "Schitt's Creek", "Gilmore Girls", "The Good Place",
        "Parks and Recreation", "Bluey", "Heartstopper", "Friday Night Lights",
    ],
    "horror_dread": [
        "Hannibal", "The Haunting of Hill House", "Midnight Mass",
        "Stranger Things", "The X-Files", "Twin Peaks",
    ],
    "melancholy_longing": [
        "Normal People", "Fleabag", "BoJack Horseman", "After Life",
        "Mad Men", "Atlanta",
    ],
    "tension_thriller": [
        "Breaking Bad", "The Sopranos", "The Wire", "Better Call Saul",
        "Fargo", "Mindhunter", "True Detective",
    ],
    "awe_scifi": [
        "The Expanse", "Battlestar Galactica", "Star Trek: The Next Generation",
        "For All Mankind",
    ],
}

SHOW_ARC_TRAGIC = [
    "Chernobyl", "Mr. Robot", "The Handmaid's Tale", "Dexter", "The Sopranos",
]
SHOW_ARC_UPLIFTING = [
    "Ted Lasso", "Schitt's Creek", "The Good Place", "Parks and Recreation",
    "Bluey",
]  # Friday Night Lights excluded — its finale is warmly bittersweet, not unambiguously uplifting

SHOW_EXPECTED_DOMINANT = [
    ("Breaking Bad", "tension", 5),
    ("The Leftovers", "grief", 3),
    ("Chernobyl", "dread", 4),
    ("Ted Lasso", "warmth", 4),
    ("Schitt's Creek", "warmth", 5),
    ("Hannibal", "dread", 4),
    ("The Haunting of Hill House", "grief", 5),
    ("BoJack Horseman", "melancholy", 4),
    ("Fleabag", "melancholy", 5),
    ("The Sopranos", "tension", 5),
    ("Mad Men", "melancholy", 5),
    ("Twin Peaks", "dread", 5),
    ("The Good Place", "warmth", 6),
]
SHOW_EXPECTED_ABSENT = [
    ("Ted Lasso", "dread", 6),
    ("Schitt's Creek", "dread", 6),
    ("Bluey", "dread", 6),
]


# ===========================================================================
# ANIME ground truth (sourced; mirrors the prior media)
# ===========================================================================
# Sourcing (2026-06): cbr/earlygame (saddest/devastating anime), animehunch/cbr
# (dark psychological), collider/ranker/cbr (wholesome comfort anime).
ANIME_CLUSTERS = {
    "devastation": [
        "Clannad: After Story", "Your Lie in April", "Anohana", "Plastic Memories",
        "Made in Abyss", "Banana Fish", "86 Eighty-Six", "Wonder Egg Priority",
    ],
    "dark_psychological": [
        "Monster", "Death Note", "Tokyo Ghoul", "Neon Genesis Evangelion",
        "Psycho-Pass", "Higurashi When They Cry", "Paranoia Agent", "Berserk",
        "Attack on Titan", "Chainsaw Man", "Erased",
    ],
    "melancholy_contemplative": [
        "March Comes in Like a Lion", "Violet Evergarden", "Mushishi",
        "Cowboy Bebop", "Haibane Renmei", "Aria the Animation", "Vinland Saga",
    ],
    "cozy_wholesome": [
        "Spy x Family", "Barakamon", "Laid-Back Camp", "K-On!", "Fruits Basket",
        "Natsume's Book of Friends", "My Love Story!!", "Sweetness and Lightning",
    ],
    "adventure_triumph": [
        "Fullmetal Alchemist: Brotherhood", "Hunter x Hunter", "One Piece",
        "Mob Psycho 100", "Gurren Lagann", "My Hero Academia", "Demon Slayer",
        "Jujutsu Kaisen", "Code Geass",
    ],
    "comedy": [
        "Gintama", "One Punch Man", "Nichijou", "Konosuba",
        "The Disastrous Life of Saiki K.",
    ],
}
ANIME_ARC_TRAGIC = [
    "Your Lie in April", "Plastic Memories", "Banana Fish",
    "Neon Genesis Evangelion", "Berserk",
]
ANIME_ARC_UPLIFTING = [
    "Fullmetal Alchemist: Brotherhood", "My Hero Academia", "Gurren Lagann",
    "Mob Psycho 100", "K-On!", "Barakamon",
]
ANIME_EXPECTED_DOMINANT = [
    ("Your Lie in April", "melancholy", 4),
    ("Clannad: After Story", "grief", 4),
    ("Monster", "tension", 5),
    ("Death Note", "tension", 5),
    ("Berserk", "dread", 4),
    ("K-On!", "joy", 5),
    ("Spy x Family", "warmth", 5),
    ("Cowboy Bebop", "melancholy", 5),
    ("Neon Genesis Evangelion", "dread", 5),
    ("Gurren Lagann", "empowerment", 5),
]
ANIME_EXPECTED_ABSENT = [
    ("K-On!", "dread", 6),
    ("Barakamon", "dread", 6),
    ("Spy x Family", "grief", 6),
]

# ===========================================================================
# MANGA ground truth (sourced; mirrors the prior media)
# ===========================================================================
# Sourcing (2026-06): animesenpai/gamerant/collider (dark/horror manga),
# cbr top psychological manga, plus general consensus. Manga endings are fuzzy
# (long-running) → ARC sets kept to clearly-resolved works.
MANGA_CLUSTERS = {
    "devastation": [
        "Goodnight Punpun", "A Silent Voice", "Vinland Saga", "Attack on Titan",
        "Berserk", "Vagabond", "Solanin",
    ],
    "dark_psychological": [
        "Monster", "Death Note", "Tokyo Ghoul", "Homunculus", "The Flowers of Evil",
        "20th Century Boys", "Inuyashiki", "Chainsaw Man", "Parasyte", "I Am a Hero",
    ],
    "horror": [
        "Uzumaki", "Tomie", "The Drifting Classroom", "Gyo", "Dorohedoro",
    ],
    "melancholy_literary": [
        "Blue Period", "Mushishi", "A Drifting Life", "A Distant Neighborhood", "Nana",
    ],
    "cozy_wholesome": [
        "Spy x Family", "Komi Can't Communicate", "Barakamon", "Fruits Basket",
        "Sweetness and Lightning", "Yotsuba&!", "Witch Hat Atelier",
    ],
    "adventure_triumph": [
        "One Piece", "Fullmetal Alchemist", "Hunter x Hunter", "Demon Slayer",
        "Jujutsu Kaisen", "Slam Dunk", "Pluto", "Naruto",
    ],
}
MANGA_ARC_TRAGIC = [
    "Goodnight Punpun", "Berserk", "Homunculus",
]  # The Flowers of Evil excluded — its manga ending is bittersweet/hopeful, not bleak
MANGA_ARC_UPLIFTING = [
    "Fullmetal Alchemist", "Slam Dunk", "Witch Hat Atelier",
]
MANGA_EXPECTED_DOMINANT = [
    ("Goodnight Punpun", "melancholy", 5),
    ("Berserk", "dread", 4),
    ("Uzumaki", "dread", 3),
    ("Monster", "tension", 5),
    ("A Silent Voice", "grief", 5),
    ("Yotsuba&!", "warmth", 5),
    ("Tomie", "dread", 3),
    ("Vinland Saga", "grief", 6),
]
MANGA_EXPECTED_ABSENT = [
    ("Yotsuba&!", "dread", 6),
    ("Komi Can't Communicate", "dread", 6),
]


# ===========================================================================
# VIDEO GAME ground truth (sourced; mirrors the prior media)
# ===========================================================================
# Sourcing (2026-06): gaming.net/ranker/comicbook (emotional games), thegamer/
# gamerant (atmospheric-horror games), eneba/gamespot/cnn (cozy games).
GAME_CLUSTERS = {
    "devastation": [
        "The Last of Us", "Red Dead Redemption 2", "To the Moon",
        "What Remains of Edith Finch", "That Dragon, Cancer",
        "Brothers: A Tale of Two Sons", "Spec Ops: The Line", "Final Fantasy VII",
    ],
    "horror_dread": [
        "Silent Hill 2", "Resident Evil 2", "Bloodborne", "Dead Space",
        "Amnesia: The Dark Descent", "SOMA", "Alien: Isolation", "Outlast",
    ],
    "melancholy_contemplative": [
        "Disco Elysium", "Hollow Knight", "Gris", "Firewatch",
        "Kentucky Route Zero", "NieR: Automata", "Night in the Woods",
    ],
    "cozy_wholesome": [
        "Stardew Valley", "Animal Crossing: New Horizons", "Spiritfarer",
        "A Short Hike", "Untitled Goose Game", "Slime Rancher", "Unpacking",
    ],
    "wonder_adventure": [
        "Outer Wilds", "Journey", "The Legend of Zelda: Breath of the Wild",
        "Subnautica", "Portal", "Abzu", "No Man's Sky",
    ],
    "triumph": [
        "Celeste", "Hades", "God of War", "Doom Eternal",
        "Ori and the Blind Forest", "Sekiro: Shadows Die Twice",
    ],
    "dark_oppressive": [
        "Dark Souls", "Elden Ring", "Inside", "Limbo",
    ],
}
GAME_ARC_TRAGIC = [
    "Red Dead Redemption 2", "Spec Ops: The Line", "The Last of Us",
    "Brothers: A Tale of Two Sons",
]
GAME_ARC_UPLIFTING = [
    "Celeste", "Ori and the Blind Forest", "A Short Hike", "Hades",
]
GAME_EXPECTED_DOMINANT = [
    ("The Last of Us", "grief", 5),
    ("Red Dead Redemption 2", "melancholy", 5),
    ("Silent Hill 2", "dread", 3),
    ("Amnesia: The Dark Descent", "dread", 3),
    ("Stardew Valley", "warmth", 5),
    ("Disco Elysium", "melancholy", 5),
    ("Outer Wilds", "wonder", 4),
    ("Journey", "wonder", 4),
    ("Hades", "empowerment", 5),
    ("Spiritfarer", "grief", 5),
    ("Hollow Knight", "melancholy", 5),
]
GAME_EXPECTED_ABSENT = [
    ("Stardew Valley", "dread", 6),
    ("Animal Crossing: New Horizons", "dread", 6),
    ("A Short Hike", "dread", 6),
]


# --- similarity helpers (operate on a `corpus` fixture — any medium) ---------
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
    """Replicate the production /recommend ranking against the loaded corpus, using
    the per-emotion taste-profile model.

    `ratings` stays a list of (title, star) tuples so the test files are unchanged.
    A high star is treated as the user LIKING that work's most-prevalent felt
    emotions (+1), a low star as DISLIKING them (-1) — exactly the signal the new UI
    collects. We aggregate a taste-profile weight vector (build_taste_profile) and
    rank the rest of the corpus by cosine against the standardized vectors, like the
    real endpoint.
    """
    from app.dimensions import STRUCTURAL_KEYS
    from app.services.feedback import build_taste_profile

    feedback_maps = []
    rated = set()
    for title, star in ratings:
        rated.add(title)
        mark = 1 if star >= 3.5 else (-1 if star <= 2.5 else 0)
        if mark == 0:
            continue
        scores = corpus[title]["scores"]
        top = sorted(
            (key for key in scores if key not in STRUCTURAL_KEYS),
            key=lambda key: -scores[key],
        )[:6]
        feedback_maps.append({key: mark for key in top})

    weights = build_taste_profile(feedback_maps)
    norm = float(np.linalg.norm(weights))
    if norm == 0:
        return []
    weights = weights / norm
    ranked = sorted(
        ((cosine(weights, corpus[t]["vec"]), t) for t in corpus if t not in rated),
        reverse=True,
    )
    return [t for _, t in ranked[:k]]


# Targets / penalty weight mirror app/routers/recommend.py (experience search).
_ENDING_TARGETS = {"bleak": 0.15, "bittersweet": 0.5, "uplifting": 0.85}
_LAMBDA_END = 0.25


def mood_recommend(
    corpus: dict,
    seek=(),
    avoid=(),
    ending: str = "any",
    ratings=(),
    alpha: float = 0.6,
    k: int = 10,
) -> list:
    """Replicate the production experience-search ranking against the loaded corpus.

    Build a mood direction from seek/avoid feelings, blend it with an optional taste
    profile (from `(title, star)` ratings, encoded like `preference_recommend`) via
    the alpha dial, rank by cosine against the standardized vectors, then lean toward
    `ending` with the same soft penalty on raw ending_valence the endpoint applies.
    """
    from app.dimensions import STRUCTURAL_KEYS
    from app.services.feedback import build_taste_profile
    from app.services.mood import blend_vectors, build_mood_vector

    mood = {key: 1 for key in seek}
    mood.update({key: -1 for key in avoid})
    mood_vec = build_mood_vector(mood)

    feedback_maps = []
    rated = set()
    for title, star in ratings:
        rated.add(title)
        mark = 1 if star >= 3.5 else (-1 if star <= 2.5 else 0)
        if mark == 0:
            continue
        scores = corpus[title]["scores"]
        top = sorted(
            (key for key in scores if key not in STRUCTURAL_KEYS),
            key=lambda key: -scores[key],
        )[:6]
        feedback_maps.append({key: mark for key in top})
    taste = build_taste_profile(feedback_maps)

    query = blend_vectors(mood_vec, taste, alpha)
    if float(np.linalg.norm(query)) == 0:
        return []

    def score(title: str) -> float:
        c = cosine(query, corpus[title]["vec"])
        if ending == "any":
            return c
        ev = corpus[title]["scores"].get("ending_valence", 0.5)
        return c - _LAMBDA_END * abs(ev - _ENDING_TARGETS[ending])

    ranked = sorted(((score(t), t) for t in corpus if t not in rated), reverse=True)
    return [t for _, t in ranked[:k]]
