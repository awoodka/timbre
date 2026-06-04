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


SEED_SHOWS = [
    # --- Devastation / grief ---
    {"title": "The Leftovers", "creator": "Damon Lindelof", "metadata_": {"year": 2014, "genre": ["drama"]}},
    {"title": "Band of Brothers", "creator": "Steven Spielberg", "metadata_": {"year": 2001, "genre": ["war", "drama"]}},
    {"title": "Chernobyl", "creator": "Craig Mazin", "metadata_": {"year": 2019, "genre": ["drama", "history"]}},
    {"title": "Six Feet Under", "creator": "Alan Ball", "metadata_": {"year": 2001, "genre": ["drama"]}},
    {"title": "When They See Us", "creator": "Ava DuVernay", "metadata_": {"year": 2019, "genre": ["drama", "crime"]}},
    {"title": "This Is Us", "creator": "Dan Fogelman", "metadata_": {"year": 2016, "genre": ["drama"]}},

    # --- Prestige / moral / tension ---
    {"title": "Breaking Bad", "creator": "Vince Gilligan", "metadata_": {"year": 2008, "genre": ["drama", "crime"]}},
    {"title": "The Sopranos", "creator": "David Chase", "metadata_": {"year": 1999, "genre": ["drama", "crime"]}},
    {"title": "The Wire", "creator": "David Simon", "metadata_": {"year": 2002, "genre": ["drama", "crime"]}},
    {"title": "Better Call Saul", "creator": "Vince Gilligan", "metadata_": {"year": 2015, "genre": ["drama", "crime"]}},
    {"title": "Mad Men", "creator": "Matthew Weiner", "metadata_": {"year": 2007, "genre": ["drama"]}},
    {"title": "Succession", "creator": "Jesse Armstrong", "metadata_": {"year": 2018, "genre": ["drama"]}},

    # --- Cosmic / atmospheric / horror ---
    {"title": "Twin Peaks", "creator": "David Lynch", "metadata_": {"year": 1990, "genre": ["drama", "mystery"]}},
    {"title": "The X-Files", "creator": "Chris Carter", "metadata_": {"year": 1993, "genre": ["science fiction", "mystery"]}},
    {"title": "Hannibal", "creator": "Bryan Fuller", "metadata_": {"year": 2013, "genre": ["drama", "horror", "thriller"]}},
    {"title": "The Haunting of Hill House", "creator": "Mike Flanagan", "metadata_": {"year": 2018, "genre": ["horror", "drama"]}},
    {"title": "Stranger Things", "creator": "The Duffer Brothers", "metadata_": {"year": 2016, "genre": ["science fiction", "horror"]}},
    {"title": "Dark", "creator": "Baran bo Odar", "metadata_": {"year": 2017, "genre": ["science fiction", "mystery"]}},
    {"title": "Severance", "creator": "Dan Erickson", "metadata_": {"year": 2022, "genre": ["science fiction", "thriller", "drama"]}},
    {"title": "True Detective", "creator": "Nic Pizzolatto", "metadata_": {"year": 2014, "genre": ["crime", "drama", "mystery"]}},
    {"title": "Midnight Mass", "creator": "Mike Flanagan", "metadata_": {"year": 2021, "genre": ["horror", "drama"]}},

    # --- Dystopia / dark-speculative ---
    {"title": "Black Mirror", "creator": "Charlie Brooker", "metadata_": {"year": 2011, "genre": ["science fiction", "drama"]}},
    {"title": "The Handmaid's Tale", "creator": "Bruce Miller", "metadata_": {"year": 2017, "genre": ["science fiction", "drama"]}},
    {"title": "Watchmen", "creator": "Damon Lindelof", "metadata_": {"year": 2019, "genre": ["drama", "science fiction"]}},
    {"title": "Mr. Robot", "creator": "Sam Esmail", "metadata_": {"year": 2015, "genre": ["drama", "thriller"]}},

    # --- Melancholy / longing ---
    {"title": "Normal People", "creator": "Sally Rooney", "metadata_": {"year": 2020, "genre": ["drama", "romance"]}},
    {"title": "Fleabag", "creator": "Phoebe Waller-Bridge", "metadata_": {"year": 2016, "genre": ["comedy", "drama"]}},
    {"title": "BoJack Horseman", "creator": "Raphael Bob-Waksberg", "metadata_": {"year": 2014, "genre": ["animation", "comedy", "drama"]}},
    {"title": "After Life", "creator": "Ricky Gervais", "metadata_": {"year": 2019, "genre": ["comedy", "drama"]}},
    {"title": "Atlanta", "creator": "Donald Glover", "metadata_": {"year": 2016, "genre": ["comedy", "drama"]}},

    # --- Cozy / warm / feel-good ---
    {"title": "Ted Lasso", "creator": "Bill Lawrence", "metadata_": {"year": 2020, "genre": ["comedy", "drama"]}},
    {"title": "Schitt's Creek", "creator": "Dan Levy", "metadata_": {"year": 2015, "genre": ["comedy"]}},
    {"title": "Gilmore Girls", "creator": "Amy Sherman-Palladino", "metadata_": {"year": 2000, "genre": ["comedy", "drama"]}},
    {"title": "The Good Place", "creator": "Michael Schur", "metadata_": {"year": 2016, "genre": ["comedy"]}},
    {"title": "Parks and Recreation", "creator": "Greg Daniels", "metadata_": {"year": 2009, "genre": ["comedy"]}},
    {"title": "Bluey", "creator": "Joe Brumm", "metadata_": {"year": 2018, "genre": ["animation", "family"]}},
    {"title": "Friday Night Lights", "creator": "Peter Berg", "metadata_": {"year": 2006, "genre": ["drama"]}},
    {"title": "Heartstopper", "creator": "Alice Oseman", "metadata_": {"year": 2022, "genre": ["drama", "romance"]}},

    # --- Awe / sci-fi sublime ---
    {"title": "The Expanse", "creator": "Mark Fergus", "metadata_": {"year": 2015, "genre": ["science fiction", "drama"]}},
    {"title": "Battlestar Galactica", "creator": "Ronald D. Moore", "metadata_": {"year": 2004, "genre": ["science fiction", "drama"]}},
    {"title": "Star Trek: The Next Generation", "creator": "Gene Roddenberry", "metadata_": {"year": 1987, "genre": ["science fiction"]}},
    {"title": "For All Mankind", "creator": "Ronald D. Moore", "metadata_": {"year": 2019, "genre": ["science fiction", "drama"]}},

    # --- Tension / thriller / crime ---
    {"title": "Fargo", "creator": "Noah Hawley", "metadata_": {"year": 2014, "genre": ["crime", "drama"]}},
    {"title": "Mindhunter", "creator": "Joe Penhall", "metadata_": {"year": 2017, "genre": ["crime", "drama", "thriller"]}},
    {"title": "Sherlock", "creator": "Steven Moffat", "metadata_": {"year": 2010, "genre": ["crime", "drama", "mystery"]}},
    {"title": "Dexter", "creator": "James Manos Jr.", "metadata_": {"year": 2006, "genre": ["crime", "drama"]}},

    # --- Comedy / absurd ---
    {"title": "Community", "creator": "Dan Harmon", "metadata_": {"year": 2009, "genre": ["comedy"]}},
    {"title": "It's Always Sunny in Philadelphia", "creator": "Rob McElhenney", "metadata_": {"year": 2005, "genre": ["comedy"]}},
    {"title": "Arrested Development", "creator": "Mitchell Hurwitz", "metadata_": {"year": 2003, "genre": ["comedy"]}},
    {"title": "Rick and Morty", "creator": "Dan Harmon", "metadata_": {"year": 2013, "genre": ["animation", "science fiction", "comedy"]}},
]


SEED_ANIME = [
    # --- Devastation / tragedy ---
    {"title": "Clannad: After Story", "creator": "Kyoto Animation", "metadata_": {"year": 2008, "genre": ["drama", "romance"]}},
    {"title": "Your Lie in April", "creator": "A-1 Pictures", "metadata_": {"year": 2014, "genre": ["drama", "romance", "music"]}},
    {"title": "Anohana", "creator": "A-1 Pictures", "metadata_": {"year": 2011, "genre": ["drama"]}},
    {"title": "Plastic Memories", "creator": "Doga Kobo", "metadata_": {"year": 2015, "genre": ["drama", "science fiction", "romance"]}},
    {"title": "Made in Abyss", "creator": "Kinema Citrus", "metadata_": {"year": 2017, "genre": ["adventure", "fantasy", "drama"]}},
    {"title": "Banana Fish", "creator": "MAPPA", "metadata_": {"year": 2018, "genre": ["drama", "crime"]}},
    {"title": "86 Eighty-Six", "creator": "A-1 Pictures", "metadata_": {"year": 2021, "genre": ["drama", "science fiction"]}},
    {"title": "Wonder Egg Priority", "creator": "CloverWorks", "metadata_": {"year": 2021, "genre": ["drama", "psychological"]}},

    # --- Dark / psychological ---
    {"title": "Monster", "creator": "Madhouse", "metadata_": {"year": 2004, "genre": ["thriller", "psychological", "drama"]}},
    {"title": "Death Note", "creator": "Madhouse", "metadata_": {"year": 2006, "genre": ["thriller", "psychological"]}},
    {"title": "Tokyo Ghoul", "creator": "Studio Pierrot", "metadata_": {"year": 2014, "genre": ["horror", "psychological", "action"]}},
    {"title": "Neon Genesis Evangelion", "creator": "Gainax", "metadata_": {"year": 1995, "genre": ["science fiction", "psychological", "mecha"]}},
    {"title": "Psycho-Pass", "creator": "Production I.G", "metadata_": {"year": 2012, "genre": ["science fiction", "psychological", "thriller"]}},
    {"title": "Higurashi When They Cry", "creator": "Studio Deen", "metadata_": {"year": 2006, "genre": ["horror", "mystery", "psychological"]}},
    {"title": "Paranoia Agent", "creator": "Madhouse", "metadata_": {"year": 2004, "genre": ["psychological", "mystery"]}},
    {"title": "Berserk", "creator": "OLM", "metadata_": {"year": 1997, "genre": ["dark fantasy", "action", "horror"]}},
    {"title": "Attack on Titan", "creator": "Wit Studio", "metadata_": {"year": 2013, "genre": ["action", "drama", "dark fantasy"]}},
    {"title": "Chainsaw Man", "creator": "MAPPA", "metadata_": {"year": 2022, "genre": ["action", "horror", "dark fantasy"]}},
    {"title": "Erased", "creator": "A-1 Pictures", "metadata_": {"year": 2016, "genre": ["thriller", "mystery", "drama"]}},

    # --- Melancholy / contemplative ---
    {"title": "March Comes in Like a Lion", "creator": "Shaft", "metadata_": {"year": 2016, "genre": ["drama", "slice of life"]}},
    {"title": "Violet Evergarden", "creator": "Kyoto Animation", "metadata_": {"year": 2018, "genre": ["drama", "fantasy"]}},
    {"title": "Mushishi", "creator": "Artland", "metadata_": {"year": 2005, "genre": ["supernatural", "slice of life", "mystery"]}},
    {"title": "Cowboy Bebop", "creator": "Sunrise", "metadata_": {"year": 1998, "genre": ["science fiction", "action", "neo-noir"]}},
    {"title": "Haibane Renmei", "creator": "Radix", "metadata_": {"year": 2002, "genre": ["drama", "supernatural", "mystery"]}},
    {"title": "Aria the Animation", "creator": "Hal Film Maker", "metadata_": {"year": 2005, "genre": ["slice of life", "fantasy"]}},
    {"title": "Vinland Saga", "creator": "Wit Studio", "metadata_": {"year": 2019, "genre": ["action", "drama", "historical"]}},

    # --- Cozy / wholesome ---
    {"title": "Spy x Family", "creator": "Wit Studio", "metadata_": {"year": 2022, "genre": ["comedy", "action", "slice of life"]}},
    {"title": "Barakamon", "creator": "Kinema Citrus", "metadata_": {"year": 2014, "genre": ["comedy", "slice of life"]}},
    {"title": "Laid-Back Camp", "creator": "C-Station", "metadata_": {"year": 2018, "genre": ["slice of life", "comedy"]}},
    {"title": "K-On!", "creator": "Kyoto Animation", "metadata_": {"year": 2009, "genre": ["comedy", "music", "slice of life"]}},
    {"title": "Fruits Basket", "creator": "TMS Entertainment", "metadata_": {"year": 2019, "genre": ["drama", "romance", "supernatural"]}},
    {"title": "Natsume's Book of Friends", "creator": "Brain's Base", "metadata_": {"year": 2008, "genre": ["supernatural", "slice of life", "drama"]}},
    {"title": "My Love Story!!", "creator": "Madhouse", "metadata_": {"year": 2015, "genre": ["romance", "comedy"]}},
    {"title": "Sweetness and Lightning", "creator": "TMS Entertainment", "metadata_": {"year": 2016, "genre": ["slice of life", "comedy"]}},

    # --- Wonder / adventure / triumph ---
    {"title": "Fullmetal Alchemist: Brotherhood", "creator": "Bones", "metadata_": {"year": 2009, "genre": ["action", "adventure", "fantasy", "drama"]}},
    {"title": "Hunter x Hunter", "creator": "Madhouse", "metadata_": {"year": 2011, "genre": ["action", "adventure", "fantasy"]}},
    {"title": "One Piece", "creator": "Toei Animation", "metadata_": {"year": 1999, "genre": ["action", "adventure", "fantasy"]}},
    {"title": "Mob Psycho 100", "creator": "Bones", "metadata_": {"year": 2016, "genre": ["action", "comedy", "supernatural"]}},
    {"title": "Gurren Lagann", "creator": "Gainax", "metadata_": {"year": 2007, "genre": ["action", "science fiction", "mecha"]}},
    {"title": "My Hero Academia", "creator": "Bones", "metadata_": {"year": 2016, "genre": ["action", "superhero"]}},
    {"title": "Demon Slayer", "creator": "ufotable", "metadata_": {"year": 2019, "genre": ["action", "dark fantasy"]}},
    {"title": "Jujutsu Kaisen", "creator": "MAPPA", "metadata_": {"year": 2020, "genre": ["action", "dark fantasy"]}},
    {"title": "Steins;Gate", "creator": "White Fox", "metadata_": {"year": 2011, "genre": ["science fiction", "thriller", "drama"]}},
    {"title": "Code Geass", "creator": "Sunrise", "metadata_": {"year": 2006, "genre": ["mecha", "drama", "thriller"]}},

    # --- Comedy / absurd ---
    {"title": "Gintama", "creator": "Sunrise", "metadata_": {"year": 2006, "genre": ["comedy", "action", "science fiction"]}},
    {"title": "One Punch Man", "creator": "Madhouse", "metadata_": {"year": 2015, "genre": ["action", "comedy", "superhero"]}},
    {"title": "Nichijou", "creator": "Kyoto Animation", "metadata_": {"year": 2011, "genre": ["comedy", "slice of life"]}},
    {"title": "Konosuba", "creator": "Studio Deen", "metadata_": {"year": 2016, "genre": ["comedy", "fantasy", "isekai"]}},
    {"title": "The Disastrous Life of Saiki K.", "creator": "J.C.Staff", "metadata_": {"year": 2016, "genre": ["comedy", "supernatural"]}},
    {"title": "Toradora", "creator": "J.C.Staff", "metadata_": {"year": 2008, "genre": ["romance", "comedy", "drama"]}},
]

SEED_MANGA = [
    # --- Devastation / tragedy ---
    {"title": "Goodnight Punpun", "creator": "Inio Asano", "metadata_": {"year": 2007, "genre": ["drama", "slice of life", "psychological"]}},
    {"title": "A Silent Voice", "creator": "Yoshitoki Oima", "metadata_": {"year": 2013, "genre": ["drama", "romance"]}},
    {"title": "Vinland Saga", "creator": "Makoto Yukimura", "metadata_": {"year": 2005, "genre": ["action", "drama", "historical"]}},
    {"title": "Attack on Titan", "creator": "Hajime Isayama", "metadata_": {"year": 2009, "genre": ["action", "drama", "dark fantasy"]}},
    {"title": "Berserk", "creator": "Kentaro Miura", "metadata_": {"year": 1989, "genre": ["dark fantasy", "action", "horror"]}},
    {"title": "Vagabond", "creator": "Takehiko Inoue", "metadata_": {"year": 1998, "genre": ["action", "historical", "drama"]}},
    {"title": "Solanin", "creator": "Inio Asano", "metadata_": {"year": 2005, "genre": ["drama", "slice of life"]}},

    # --- Dark / psychological ---
    {"title": "Monster", "creator": "Naoki Urasawa", "metadata_": {"year": 1994, "genre": ["thriller", "psychological", "drama"]}},
    {"title": "Death Note", "creator": "Tsugumi Ohba", "metadata_": {"year": 2003, "genre": ["thriller", "psychological"]}},
    {"title": "Tokyo Ghoul", "creator": "Sui Ishida", "metadata_": {"year": 2011, "genre": ["horror", "psychological", "action"]}},
    {"title": "Homunculus", "creator": "Hideo Yamamoto", "metadata_": {"year": 2003, "genre": ["psychological", "drama"]}},
    {"title": "The Flowers of Evil", "creator": "Shuzo Oshimi", "metadata_": {"year": 2009, "genre": ["psychological", "drama"]}},
    {"title": "20th Century Boys", "creator": "Naoki Urasawa", "metadata_": {"year": 1999, "genre": ["thriller", "mystery", "science fiction"]}},
    {"title": "Inuyashiki", "creator": "Hiroya Oku", "metadata_": {"year": 2014, "genre": ["science fiction", "drama", "action"]}},
    {"title": "Chainsaw Man", "creator": "Tatsuki Fujimoto", "metadata_": {"year": 2018, "genre": ["action", "horror", "dark fantasy"]}},
    {"title": "Parasyte", "creator": "Hitoshi Iwaaki", "metadata_": {"year": 1988, "genre": ["horror", "science fiction", "psychological"]}},
    {"title": "I Am a Hero", "creator": "Kengo Hanazawa", "metadata_": {"year": 2009, "genre": ["horror", "psychological"]}},

    # --- Horror ---
    {"title": "Uzumaki", "creator": "Junji Ito", "metadata_": {"year": 1998, "genre": ["horror"]}},
    {"title": "Tomie", "creator": "Junji Ito", "metadata_": {"year": 1987, "genre": ["horror"]}},
    {"title": "The Drifting Classroom", "creator": "Kazuo Umezu", "metadata_": {"year": 1972, "genre": ["horror", "drama"]}},
    {"title": "Gyo", "creator": "Junji Ito", "metadata_": {"year": 2001, "genre": ["horror"]}},
    {"title": "Dorohedoro", "creator": "Q Hayashida", "metadata_": {"year": 2000, "genre": ["dark fantasy", "action", "comedy"]}},

    # --- Melancholy / literary ---
    {"title": "Blue Period", "creator": "Tsubasa Yamaguchi", "metadata_": {"year": 2017, "genre": ["drama", "slice of life"]}},
    {"title": "Mushishi", "creator": "Yuki Urushibara", "metadata_": {"year": 1999, "genre": ["supernatural", "slice of life", "mystery"]}},
    {"title": "A Drifting Life", "creator": "Yoshihiro Tatsumi", "metadata_": {"year": 2008, "genre": ["drama", "autobiographical"]}},
    {"title": "A Distant Neighborhood", "creator": "Jiro Taniguchi", "metadata_": {"year": 1998, "genre": ["drama"]}},

    # --- Cozy / wholesome ---
    {"title": "Spy x Family", "creator": "Tatsuya Endo", "metadata_": {"year": 2019, "genre": ["comedy", "action", "slice of life"]}},
    {"title": "Komi Can't Communicate", "creator": "Tomohito Oda", "metadata_": {"year": 2016, "genre": ["comedy", "romance", "slice of life"]}},
    {"title": "Barakamon", "creator": "Satsuki Yoshino", "metadata_": {"year": 2008, "genre": ["comedy", "slice of life"]}},
    {"title": "Fruits Basket", "creator": "Natsuki Takaya", "metadata_": {"year": 1998, "genre": ["drama", "romance", "supernatural"]}},
    {"title": "Sweetness and Lightning", "creator": "Gido Amagakure", "metadata_": {"year": 2013, "genre": ["slice of life"]}},
    {"title": "Yotsuba&!", "creator": "Kiyohiko Azuma", "metadata_": {"year": 2003, "genre": ["comedy", "slice of life"]}},
    {"title": "Skip Beat!", "creator": "Yoshiki Nakamura", "metadata_": {"year": 2002, "genre": ["comedy", "romance", "drama"]}},

    # --- Wonder / adventure / triumph ---
    {"title": "One Piece", "creator": "Eiichiro Oda", "metadata_": {"year": 1997, "genre": ["action", "adventure", "fantasy"]}},
    {"title": "Fullmetal Alchemist", "creator": "Hiromu Arakawa", "metadata_": {"year": 2001, "genre": ["action", "adventure", "fantasy"]}},
    {"title": "Hunter x Hunter", "creator": "Yoshihiro Togashi", "metadata_": {"year": 1998, "genre": ["action", "adventure", "fantasy"]}},
    {"title": "Demon Slayer", "creator": "Koyoharu Gotouge", "metadata_": {"year": 2016, "genre": ["action", "dark fantasy"]}},
    {"title": "Jujutsu Kaisen", "creator": "Gege Akutami", "metadata_": {"year": 2018, "genre": ["action", "dark fantasy"]}},
    {"title": "Slam Dunk", "creator": "Takehiko Inoue", "metadata_": {"year": 1990, "genre": ["sports", "drama", "comedy"]}},
    {"title": "Pluto", "creator": "Naoki Urasawa", "metadata_": {"year": 2003, "genre": ["science fiction", "mystery", "drama"]}},
    {"title": "Made in Abyss", "creator": "Akihito Tsukushi", "metadata_": {"year": 2012, "genre": ["adventure", "dark fantasy"]}},
    {"title": "Naruto", "creator": "Masashi Kishimoto", "metadata_": {"year": 1999, "genre": ["action", "adventure"]}},

    # --- Comedy / absurd ---
    {"title": "One Punch Man", "creator": "ONE", "metadata_": {"year": 2012, "genre": ["action", "comedy", "superhero"]}},
    {"title": "Gintama", "creator": "Hideaki Sorachi", "metadata_": {"year": 2003, "genre": ["comedy", "action", "science fiction"]}},
    {"title": "Grand Blue", "creator": "Kenji Inoue", "metadata_": {"year": 2014, "genre": ["comedy"]}},
    {"title": "The Disastrous Life of Saiki K.", "creator": "Shuichi Aso", "metadata_": {"year": 2012, "genre": ["comedy", "supernatural"]}},

    # --- Additional (melancholy / wonder / dark) ---
    {"title": "Nana", "creator": "Ai Yazawa", "metadata_": {"year": 2000, "genre": ["drama", "romance", "music"]}},
    {"title": "Witch Hat Atelier", "creator": "Kamome Shirahama", "metadata_": {"year": 2016, "genre": ["fantasy", "adventure"]}},
    {"title": "Hellsing", "creator": "Kouta Hirano", "metadata_": {"year": 1997, "genre": ["action", "horror", "supernatural"]}},
    {"title": "Nausicaa of the Valley of the Wind", "creator": "Hayao Miyazaki", "metadata_": {"year": 1982, "genre": ["adventure", "fantasy"]}},
]


SEED_GAMES = [
    # --- Devastation / grief ---
    {"title": "The Last of Us", "creator": "Naughty Dog", "metadata_": {"year": 2013, "genre": ["action", "drama", "post-apocalyptic"]}},
    {"title": "Red Dead Redemption 2", "creator": "Rockstar Games", "metadata_": {"year": 2018, "genre": ["action", "drama", "western"]}},
    {"title": "To the Moon", "creator": "Freebird Games", "metadata_": {"year": 2011, "genre": ["adventure", "drama"]}},
    {"title": "What Remains of Edith Finch", "creator": "Giant Sparrow", "metadata_": {"year": 2017, "genre": ["adventure", "drama"]}},
    {"title": "That Dragon, Cancer", "creator": "Numinous Games", "metadata_": {"year": 2016, "genre": ["adventure", "drama"]}},
    {"title": "Brothers: A Tale of Two Sons", "creator": "Starbreeze Studios", "metadata_": {"year": 2013, "genre": ["adventure", "drama"]}},
    {"title": "Spec Ops: The Line", "creator": "Yager Development", "metadata_": {"year": 2012, "genre": ["shooter", "drama", "war"]}},
    {"title": "Final Fantasy VII", "creator": "Square", "metadata_": {"year": 1997, "genre": ["rpg", "adventure"]}},

    # --- Dread / horror ---
    {"title": "Silent Hill 2", "creator": "Konami", "metadata_": {"year": 2001, "genre": ["horror", "psychological"]}},
    {"title": "Resident Evil 2", "creator": "Capcom", "metadata_": {"year": 2019, "genre": ["horror", "action"]}},
    {"title": "Bloodborne", "creator": "FromSoftware", "metadata_": {"year": 2015, "genre": ["action rpg", "horror"]}},
    {"title": "Dead Space", "creator": "EA Redwood Shores", "metadata_": {"year": 2008, "genre": ["horror", "action"]}},
    {"title": "Amnesia: The Dark Descent", "creator": "Frictional Games", "metadata_": {"year": 2010, "genre": ["horror"]}},
    {"title": "SOMA", "creator": "Frictional Games", "metadata_": {"year": 2015, "genre": ["horror", "science fiction"]}},
    {"title": "Alien: Isolation", "creator": "Creative Assembly", "metadata_": {"year": 2014, "genre": ["horror", "survival"]}},
    {"title": "Outlast", "creator": "Red Barrels", "metadata_": {"year": 2013, "genre": ["horror"]}},

    # --- Melancholy / contemplative ---
    {"title": "Disco Elysium", "creator": "ZA/UM", "metadata_": {"year": 2019, "genre": ["rpg", "mystery"]}},
    {"title": "Hollow Knight", "creator": "Team Cherry", "metadata_": {"year": 2017, "genre": ["metroidvania", "action"]}},
    {"title": "Gris", "creator": "Nomada Studio", "metadata_": {"year": 2018, "genre": ["platformer", "adventure"]}},
    {"title": "Firewatch", "creator": "Campo Santo", "metadata_": {"year": 2016, "genre": ["adventure", "mystery"]}},
    {"title": "Kentucky Route Zero", "creator": "Cardboard Computer", "metadata_": {"year": 2013, "genre": ["adventure"]}},
    {"title": "NieR: Automata", "creator": "PlatinumGames", "metadata_": {"year": 2017, "genre": ["action rpg"]}},
    {"title": "Night in the Woods", "creator": "Infinite Fall", "metadata_": {"year": 2017, "genre": ["adventure", "drama"]}},

    # --- Cozy / wholesome ---
    {"title": "Stardew Valley", "creator": "ConcernedApe", "metadata_": {"year": 2016, "genre": ["simulation", "rpg"]}},
    {"title": "Animal Crossing: New Horizons", "creator": "Nintendo", "metadata_": {"year": 2020, "genre": ["simulation"]}},
    {"title": "Spiritfarer", "creator": "Thunder Lotus Games", "metadata_": {"year": 2020, "genre": ["management", "adventure"]}},
    {"title": "A Short Hike", "creator": "adamgryu", "metadata_": {"year": 2019, "genre": ["adventure"]}},
    {"title": "Untitled Goose Game", "creator": "House House", "metadata_": {"year": 2019, "genre": ["puzzle", "comedy"]}},
    {"title": "Slime Rancher", "creator": "Monomi Park", "metadata_": {"year": 2017, "genre": ["simulation", "adventure"]}},
    {"title": "Unpacking", "creator": "Witch Beam", "metadata_": {"year": 2021, "genre": ["puzzle", "simulation"]}},

    # --- Wonder / awe / adventure ---
    {"title": "Outer Wilds", "creator": "Mobius Digital", "metadata_": {"year": 2019, "genre": ["adventure", "mystery", "science fiction"]}},
    {"title": "Journey", "creator": "thatgamecompany", "metadata_": {"year": 2012, "genre": ["adventure"]}},
    {"title": "The Legend of Zelda: Breath of the Wild", "creator": "Nintendo", "metadata_": {"year": 2017, "genre": ["action", "adventure"]}},
    {"title": "Subnautica", "creator": "Unknown Worlds", "metadata_": {"year": 2018, "genre": ["survival", "adventure"]}},
    {"title": "Portal", "creator": "Valve", "metadata_": {"year": 2007, "genre": ["puzzle", "science fiction"]}},
    {"title": "Abzu", "creator": "Giant Squid", "metadata_": {"year": 2016, "genre": ["adventure"]}},
    {"title": "No Man's Sky", "creator": "Hello Games", "metadata_": {"year": 2016, "genre": ["survival", "adventure", "science fiction"]}},

    # --- Triumph / empowerment ---
    {"title": "Celeste", "creator": "Maddy Makes Games", "metadata_": {"year": 2018, "genre": ["platformer"]}},
    {"title": "Hades", "creator": "Supergiant Games", "metadata_": {"year": 2020, "genre": ["roguelike", "action"]}},
    {"title": "God of War", "creator": "Santa Monica Studio", "metadata_": {"year": 2018, "genre": ["action", "adventure"]}},
    {"title": "Doom Eternal", "creator": "id Software", "metadata_": {"year": 2020, "genre": ["shooter", "action"]}},
    {"title": "Ori and the Blind Forest", "creator": "Moon Studios", "metadata_": {"year": 2015, "genre": ["platformer", "adventure"]}},
    {"title": "Sekiro: Shadows Die Twice", "creator": "FromSoftware", "metadata_": {"year": 2019, "genre": ["action", "adventure"]}},

    # --- Dark / oppressive + tension ---
    {"title": "Dark Souls", "creator": "FromSoftware", "metadata_": {"year": 2011, "genre": ["action rpg"]}},
    {"title": "Elden Ring", "creator": "FromSoftware", "metadata_": {"year": 2022, "genre": ["action rpg"]}},
    {"title": "Inside", "creator": "Playdead", "metadata_": {"year": 2016, "genre": ["puzzle", "platformer"]}},
    {"title": "Limbo", "creator": "Playdead", "metadata_": {"year": 2010, "genre": ["puzzle", "platformer"]}},
    {"title": "Metal Gear Solid", "creator": "Konami", "metadata_": {"year": 1998, "genre": ["stealth", "action"]}},
    {"title": "Return of the Obra Dinn", "creator": "Lucas Pope", "metadata_": {"year": 2018, "genre": ["puzzle", "mystery"]}},
    {"title": "Cyberpunk 2077", "creator": "CD Projekt Red", "metadata_": {"year": 2020, "genre": ["rpg", "action", "science fiction"]}},
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
        ] + [
            ("show", s["title"], s["creator"], s["metadata_"]) for s in SEED_SHOWS
        ] + [
            ("anime", a["title"], a["creator"], a["metadata_"]) for a in SEED_ANIME
        ] + [
            ("manga", m["title"], m["creator"], m["metadata_"]) for m in SEED_MANGA
        ] + [
            ("game", g["title"], g["creator"], g["metadata_"]) for g in SEED_GAMES
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
