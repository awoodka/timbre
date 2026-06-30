"""
Seed script: populates the database with a cross-media corpus of well-known
books, films, shows, anime, manga, and games.

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

    # --- Popular / mainstream additions (broad first-visit appeal) ---
    {"title": "Harry Potter and the Sorcerer's Stone", "author": "J.K. Rowling", "metadata_": {"year": 1997, "genre": ["fantasy", "young adult"]}},
    {"title": "The Hunger Games", "author": "Suzanne Collins", "metadata_": {"year": 2008, "genre": ["dystopian", "young adult"]}},
    {"title": "The Fault in Our Stars", "author": "John Green", "metadata_": {"year": 2012, "genre": ["young adult", "romance"]}},
    {"title": "The Da Vinci Code", "author": "Dan Brown", "metadata_": {"year": 2003, "genre": ["thriller", "mystery"]}},
    {"title": "The Kite Runner", "author": "Khaled Hosseini", "metadata_": {"year": 2003, "genre": ["literary fiction", "historical"]}},
    {"title": "The Alchemist", "author": "Paulo Coelho", "metadata_": {"year": 1988, "genre": ["fiction", "philosophical"]}},
    {"title": "Pride and Prejudice", "author": "Jane Austen", "metadata_": {"year": 1813, "genre": ["classic", "romance"]}},
    {"title": "Jane Eyre", "author": "Charlotte Brontë", "metadata_": {"year": 1847, "genre": ["classic", "gothic romance"]}},
    {"title": "Wuthering Heights", "author": "Emily Brontë", "metadata_": {"year": 1847, "genre": ["classic", "gothic romance"]}},
    {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien", "metadata_": {"year": 1954, "genre": ["fantasy", "epic"]}},
    {"title": "A Game of Thrones", "author": "George R.R. Martin", "metadata_": {"year": 1996, "genre": ["fantasy", "epic"]}},
    {"title": "The Lightning Thief", "author": "Rick Riordan", "metadata_": {"year": 2005, "genre": ["fantasy", "young adult"]}},
    {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson", "metadata_": {"year": 2005, "genre": ["thriller", "mystery"]}},
    {"title": "Life of Pi", "author": "Yann Martel", "metadata_": {"year": 2001, "genre": ["adventure", "literary fiction"]}},
    {"title": "The Martian", "author": "Andy Weir", "metadata_": {"year": 2011, "genre": ["science fiction", "adventure"]}},
    {"title": "Where the Crawdads Sing", "author": "Delia Owens", "metadata_": {"year": 2018, "genre": ["literary fiction", "mystery"]}},
    {"title": "The Midnight Library", "author": "Matt Haig", "metadata_": {"year": 2020, "genre": ["fiction", "fantasy"]}},
    {"title": "It", "author": "Stephen King", "metadata_": {"year": 1986, "genre": ["horror"]}},
    {"title": "The Help", "author": "Kathryn Stockett", "metadata_": {"year": 2009, "genre": ["historical fiction"]}},
    {"title": "Crime and Punishment", "author": "Fyodor Dostoevsky", "metadata_": {"year": 1866, "genre": ["classic", "psychological"]}},
    {"title": "The Brothers Karamazov", "author": "Fyodor Dostoevsky", "metadata_": {"year": 1880, "genre": ["classic", "philosophical"]}},
    {"title": "Anna Karenina", "author": "Leo Tolstoy", "metadata_": {"year": 1877, "genre": ["classic", "literary fiction"]}},
    {"title": "Moby-Dick", "author": "Herman Melville", "metadata_": {"year": 1851, "genre": ["classic", "adventure"]}},
    {"title": "The Picture of Dorian Gray", "author": "Oscar Wilde", "metadata_": {"year": 1890, "genre": ["gothic", "classic"]}},
    {"title": "Dracula", "author": "Bram Stoker", "metadata_": {"year": 1897, "genre": ["gothic", "horror"]}},
    {"title": "The Count of Monte Cristo", "author": "Alexandre Dumas", "metadata_": {"year": 1844, "genre": ["adventure", "classic"]}},
    {"title": "Les Misérables", "author": "Victor Hugo", "metadata_": {"year": 1862, "genre": ["historical", "classic"]}},
    {"title": "Little Women", "author": "Louisa May Alcott", "metadata_": {"year": 1868, "genre": ["classic", "coming-of-age"]}},
    {"title": "The Little Prince", "author": "Antoine de Saint-Exupéry", "metadata_": {"year": 1943, "genre": ["fiction", "fable"]}},
    {"title": "Of Mice and Men", "author": "John Steinbeck", "metadata_": {"year": 1937, "genre": ["literary fiction", "classic"]}},
    {"title": "The Grapes of Wrath", "author": "John Steinbeck", "metadata_": {"year": 1939, "genre": ["literary fiction", "classic"]}},
    {"title": "Lord of the Flies", "author": "William Golding", "metadata_": {"year": 1954, "genre": ["literary fiction", "classic"]}},
    {"title": "Animal Farm", "author": "George Orwell", "metadata_": {"year": 1945, "genre": ["political fiction", "satire"]}},
    {"title": "The Perks of Being a Wallflower", "author": "Stephen Chbosky", "metadata_": {"year": 1999, "genre": ["young adult", "coming-of-age"]}},
    {"title": "A Man Called Ove", "author": "Fredrik Backman", "metadata_": {"year": 2012, "genre": ["fiction", "contemporary"]}},
    {"title": "Educated", "author": "Tara Westover", "metadata_": {"year": 2018, "genre": ["memoir", "nonfiction"]}},
    {"title": "The Seven Husbands of Evelyn Hugo", "author": "Taylor Jenkins Reid", "metadata_": {"year": 2017, "genre": ["historical fiction", "romance"]}},
    {"title": "The Night Circus", "author": "Erin Morgenstern", "metadata_": {"year": 2011, "genre": ["fantasy", "romance"]}},
    {"title": "The Goldfinch", "author": "Donna Tartt", "metadata_": {"year": 2013, "genre": ["literary fiction", "coming-of-age"]}},
    {"title": "Cloud Atlas", "author": "David Mitchell", "metadata_": {"year": 2004, "genre": ["science fiction", "literary fiction"]}},
    {"title": "American Gods", "author": "Neil Gaiman", "metadata_": {"year": 2001, "genre": ["fantasy", "mythological"]}},
    {"title": "Good Omens", "author": "Neil Gaiman and Terry Pratchett", "metadata_": {"year": 1990, "genre": ["fantasy", "comedy"]}},
    {"title": "The Color Purple", "author": "Alice Walker", "metadata_": {"year": 1982, "genre": ["literary fiction", "historical"]}},
    {"title": "Fight Club", "author": "Chuck Palahniuk", "metadata_": {"year": 1996, "genre": ["literary fiction", "psychological"]}},
    {"title": "The Stranger", "author": "Albert Camus", "metadata_": {"year": 1942, "genre": ["literary fiction", "philosophical"]}},
    {"title": "The Metamorphosis", "author": "Franz Kafka", "metadata_": {"year": 1915, "genre": ["literary fiction", "absurdist"]}},
    {"title": "Pachinko", "author": "Min Jin Lee", "metadata_": {"year": 2017, "genre": ["historical fiction", "literary fiction"]}},
    {"title": "A Gentleman in Moscow", "author": "Amor Towles", "metadata_": {"year": 2016, "genre": ["historical fiction", "literary fiction"]}},
    {"title": "The Nightingale", "author": "Kristin Hannah", "metadata_": {"year": 2015, "genre": ["historical fiction", "war"]}},
    {"title": "Wonder", "author": "R.J. Palacio", "metadata_": {"year": 2012, "genre": ["young adult", "contemporary"]}},
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

    # --- Popular / mainstream additions (broad first-visit appeal) ---
    {"title": "The Lord of the Rings: The Fellowship of the Ring", "director": "Peter Jackson", "metadata_": {"year": 2001, "genre": ["fantasy", "adventure"]}},
    {"title": "The Lord of the Rings: The Return of the King", "director": "Peter Jackson", "metadata_": {"year": 2003, "genre": ["fantasy", "adventure"]}},
    {"title": "The Dark Knight", "director": "Christopher Nolan", "metadata_": {"year": 2008, "genre": ["action", "crime", "superhero"]}},
    {"title": "Inception", "director": "Christopher Nolan", "metadata_": {"year": 2010, "genre": ["science fiction", "action"]}},
    {"title": "The Matrix", "director": "The Wachowskis", "metadata_": {"year": 1999, "genre": ["science fiction", "action"]}},
    {"title": "Pulp Fiction", "director": "Quentin Tarantino", "metadata_": {"year": 1994, "genre": ["crime", "drama"]}},
    {"title": "The Godfather", "director": "Francis Ford Coppola", "metadata_": {"year": 1972, "genre": ["crime", "drama"]}},
    {"title": "Goodfellas", "director": "Martin Scorsese", "metadata_": {"year": 1990, "genre": ["crime", "drama"]}},
    {"title": "Forrest Gump", "director": "Robert Zemeckis", "metadata_": {"year": 1994, "genre": ["drama", "romance"]}},
    {"title": "Titanic", "director": "James Cameron", "metadata_": {"year": 1997, "genre": ["romance", "drama"]}},
    {"title": "Jurassic Park", "director": "Steven Spielberg", "metadata_": {"year": 1993, "genre": ["adventure", "science fiction"]}},
    {"title": "Jaws", "director": "Steven Spielberg", "metadata_": {"year": 1975, "genre": ["thriller", "horror"]}},
    {"title": "Saving Private Ryan", "director": "Steven Spielberg", "metadata_": {"year": 1998, "genre": ["war", "drama"]}},
    {"title": "Star Wars: A New Hope", "director": "George Lucas", "metadata_": {"year": 1977, "genre": ["science fiction", "adventure"]}},
    {"title": "The Empire Strikes Back", "director": "Irvin Kershner", "metadata_": {"year": 1980, "genre": ["science fiction", "adventure"]}},
    {"title": "Back to the Future", "director": "Robert Zemeckis", "metadata_": {"year": 1985, "genre": ["science fiction", "comedy"]}},
    {"title": "The Lion King", "director": "Roger Allers", "metadata_": {"year": 1994, "genre": ["animation", "family"]}},
    {"title": "Toy Story", "director": "John Lasseter", "metadata_": {"year": 1995, "genre": ["animation", "family"]}},
    {"title": "Finding Nemo", "director": "Andrew Stanton", "metadata_": {"year": 2003, "genre": ["animation", "family"]}},
    {"title": "WALL-E", "director": "Andrew Stanton", "metadata_": {"year": 2008, "genre": ["animation", "science fiction"]}},
    {"title": "Inside Out", "director": "Pete Docter", "metadata_": {"year": 2015, "genre": ["animation", "family"]}},
    {"title": "Coco", "director": "Lee Unkrich", "metadata_": {"year": 2017, "genre": ["animation", "family"]}},
    {"title": "Ratatouille", "director": "Brad Bird", "metadata_": {"year": 2007, "genre": ["animation", "family"]}},
    {"title": "The Incredibles", "director": "Brad Bird", "metadata_": {"year": 2004, "genre": ["animation", "action"]}},
    {"title": "Shrek", "director": "Andrew Adamson", "metadata_": {"year": 2001, "genre": ["animation", "comedy"]}},
    {"title": "Avengers: Endgame", "director": "Anthony Russo and Joe Russo", "metadata_": {"year": 2019, "genre": ["action", "superhero"]}},
    {"title": "Spider-Man: Into the Spider-Verse", "director": "Bob Persichetti", "metadata_": {"year": 2018, "genre": ["animation", "action", "superhero"]}},
    {"title": "Black Panther", "director": "Ryan Coogler", "metadata_": {"year": 2018, "genre": ["action", "superhero"]}},
    {"title": "Iron Man", "director": "Jon Favreau", "metadata_": {"year": 2008, "genre": ["action", "superhero"]}},
    {"title": "Gladiator", "director": "Ridley Scott", "metadata_": {"year": 2000, "genre": ["action", "drama"]}},
    {"title": "The Silence of the Lambs", "director": "Jonathan Demme", "metadata_": {"year": 1991, "genre": ["thriller", "crime", "horror"]}},
    {"title": "Fight Club", "director": "David Fincher", "metadata_": {"year": 1999, "genre": ["drama", "psychological"]}},
    {"title": "The Departed", "director": "Martin Scorsese", "metadata_": {"year": 2006, "genre": ["crime", "thriller"]}},
    {"title": "Django Unchained", "director": "Quentin Tarantino", "metadata_": {"year": 2012, "genre": ["western", "drama"]}},
    {"title": "Joker", "director": "Todd Phillips", "metadata_": {"year": 2019, "genre": ["drama", "psychological"]}},
    {"title": "La La Land", "director": "Damien Chazelle", "metadata_": {"year": 2016, "genre": ["musical", "romance"]}},
    {"title": "The Truman Show", "director": "Peter Weir", "metadata_": {"year": 1998, "genre": ["drama", "science fiction"]}},
    {"title": "Good Will Hunting", "director": "Gus Van Sant", "metadata_": {"year": 1997, "genre": ["drama"]}},
    {"title": "Slumdog Millionaire", "director": "Danny Boyle", "metadata_": {"year": 2008, "genre": ["drama", "romance"]}},
    {"title": "The Pianist", "director": "Roman Polanski", "metadata_": {"year": 2002, "genre": ["war", "drama"]}},
    {"title": "Pan's Labyrinth", "director": "Guillermo del Toro", "metadata_": {"year": 2006, "genre": ["fantasy", "war", "drama"]}},
    {"title": "Mad Max: Fury Road", "director": "George Miller", "metadata_": {"year": 2015, "genre": ["action", "science fiction"]}},
    {"title": "Everything Everywhere All at Once", "director": "Daniel Kwan and Daniel Scheinert", "metadata_": {"year": 2022, "genre": ["science fiction", "comedy", "drama"]}},
    {"title": "Get Out", "director": "Jordan Peele", "metadata_": {"year": 2017, "genre": ["horror", "thriller"]}},
    {"title": "The Green Mile", "director": "Frank Darabont", "metadata_": {"year": 1999, "genre": ["drama", "fantasy"]}},
    {"title": "Casablanca", "director": "Michael Curtiz", "metadata_": {"year": 1942, "genre": ["romance", "drama"]}},
    {"title": "How to Train Your Dragon", "director": "Dean DeBlois", "metadata_": {"year": 2010, "genre": ["animation", "fantasy", "family"]}},
    {"title": "Coraline", "director": "Henry Selick", "metadata_": {"year": 2009, "genre": ["animation", "fantasy", "horror"]}},
    {"title": "The Prestige", "director": "Christopher Nolan", "metadata_": {"year": 2006, "genre": ["drama", "mystery", "thriller"]}},
    {"title": "Inglourious Basterds", "director": "Quentin Tarantino", "metadata_": {"year": 2009, "genre": ["war", "drama"]}},
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

    # --- Popular / mainstream additions (broad first-visit appeal) ---
    {"title": "Game of Thrones", "creator": "David Benioff", "metadata_": {"year": 2011, "genre": ["fantasy", "drama"]}},
    {"title": "The Office", "creator": "Greg Daniels", "metadata_": {"year": 2005, "genre": ["comedy"]}},
    {"title": "Friends", "creator": "David Crane", "metadata_": {"year": 1994, "genre": ["comedy", "romance"]}},
    {"title": "The Crown", "creator": "Peter Morgan", "metadata_": {"year": 2016, "genre": ["drama", "history"]}},
    {"title": "The Mandalorian", "creator": "Jon Favreau", "metadata_": {"year": 2019, "genre": ["science fiction", "adventure"]}},
    {"title": "The Last of Us", "creator": "Craig Mazin", "metadata_": {"year": 2023, "genre": ["drama", "post-apocalyptic"]}},
    {"title": "Squid Game", "creator": "Hwang Dong-hyuk", "metadata_": {"year": 2021, "genre": ["thriller", "drama"]}},
    {"title": "The Witcher", "creator": "Lauren Schmidt Hissrich", "metadata_": {"year": 2019, "genre": ["fantasy", "adventure"]}},
    {"title": "Peaky Blinders", "creator": "Steven Knight", "metadata_": {"year": 2013, "genre": ["crime", "drama"]}},
    {"title": "House of the Dragon", "creator": "Ryan Condal", "metadata_": {"year": 2022, "genre": ["fantasy", "drama"]}},
    {"title": "The Boys", "creator": "Eric Kripke", "metadata_": {"year": 2019, "genre": ["superhero", "drama"]}},
    {"title": "Wednesday", "creator": "Alfred Gough", "metadata_": {"year": 2022, "genre": ["comedy", "horror", "mystery"]}},
    {"title": "Ozark", "creator": "Bill Dubuque", "metadata_": {"year": 2017, "genre": ["crime", "drama", "thriller"]}},
    {"title": "Money Heist", "creator": "Álex Pina", "metadata_": {"year": 2017, "genre": ["crime", "thriller"]}},
    {"title": "Westworld", "creator": "Jonathan Nolan", "metadata_": {"year": 2016, "genre": ["science fiction", "drama"]}},
    {"title": "Avatar: The Last Airbender", "creator": "Michael Dante DiMartino", "metadata_": {"year": 2005, "genre": ["animation", "fantasy", "adventure"]}},
    {"title": "House", "creator": "David Shore", "metadata_": {"year": 2004, "genre": ["drama", "medical"]}},
    {"title": "Lost", "creator": "J.J. Abrams", "metadata_": {"year": 2004, "genre": ["science fiction", "drama", "mystery"]}},
    {"title": "The Walking Dead", "creator": "Frank Darabont", "metadata_": {"year": 2010, "genre": ["horror", "drama"]}},
    {"title": "Seinfeld", "creator": "Larry David", "metadata_": {"year": 1989, "genre": ["comedy"]}},
    {"title": "The Big Bang Theory", "creator": "Chuck Lorre", "metadata_": {"year": 2007, "genre": ["comedy"]}},
    {"title": "How I Met Your Mother", "creator": "Carter Bays", "metadata_": {"year": 2005, "genre": ["comedy", "romance"]}},
    {"title": "Grey's Anatomy", "creator": "Shonda Rhimes", "metadata_": {"year": 2005, "genre": ["drama", "medical"]}},
    {"title": "Euphoria", "creator": "Sam Levinson", "metadata_": {"year": 2019, "genre": ["drama"]}},
    {"title": "Narcos", "creator": "Chris Brancato", "metadata_": {"year": 2015, "genre": ["crime", "drama"]}},
    {"title": "Vikings", "creator": "Michael Hirst", "metadata_": {"year": 2013, "genre": ["action", "history", "drama"]}},
    {"title": "The Umbrella Academy", "creator": "Steve Blackman", "metadata_": {"year": 2019, "genre": ["science fiction", "superhero"]}},
    {"title": "Downton Abbey", "creator": "Julian Fellowes", "metadata_": {"year": 2010, "genre": ["drama", "history"]}},
    {"title": "Sex Education", "creator": "Laurie Nunn", "metadata_": {"year": 2019, "genre": ["comedy", "drama"]}},
    {"title": "Brooklyn Nine-Nine", "creator": "Dan Goor", "metadata_": {"year": 2013, "genre": ["comedy", "crime"]}},
    {"title": "Modern Family", "creator": "Christopher Lloyd", "metadata_": {"year": 2009, "genre": ["comedy"]}},
    {"title": "The Marvelous Mrs. Maisel", "creator": "Amy Sherman-Palladino", "metadata_": {"year": 2017, "genre": ["comedy", "drama"]}},
    {"title": "The Bear", "creator": "Christopher Storer", "metadata_": {"year": 2022, "genre": ["drama", "comedy"]}},
    {"title": "The Queen's Gambit", "creator": "Scott Frank", "metadata_": {"year": 2020, "genre": ["drama"]}},
    {"title": "Yellowstone", "creator": "Taylor Sheridan", "metadata_": {"year": 2018, "genre": ["drama", "western"]}},
    {"title": "Andor", "creator": "Tony Gilroy", "metadata_": {"year": 2022, "genre": ["science fiction", "drama"]}},
    {"title": "Loki", "creator": "Michael Waldron", "metadata_": {"year": 2021, "genre": ["science fiction", "superhero"]}},
    {"title": "WandaVision", "creator": "Jac Schaeffer", "metadata_": {"year": 2021, "genre": ["superhero", "drama"]}},
    {"title": "Invincible", "creator": "Robert Kirkman", "metadata_": {"year": 2021, "genre": ["animation", "superhero", "action"]}},
    {"title": "Arcane", "creator": "Christian Linke", "metadata_": {"year": 2021, "genre": ["animation", "science fiction", "fantasy"]}},
    {"title": "Homeland", "creator": "Howard Gordon", "metadata_": {"year": 2011, "genre": ["drama", "thriller"]}},
    {"title": "Prison Break", "creator": "Paul Scheuring", "metadata_": {"year": 2005, "genre": ["action", "thriller", "crime"]}},
    {"title": "The Twilight Zone", "creator": "Rod Serling", "metadata_": {"year": 1959, "genre": ["science fiction", "anthology"]}},
    {"title": "Veep", "creator": "Armando Iannucci", "metadata_": {"year": 2012, "genre": ["comedy", "political"]}},
    {"title": "Curb Your Enthusiasm", "creator": "Larry David", "metadata_": {"year": 2000, "genre": ["comedy"]}},
    {"title": "The White Lotus", "creator": "Mike White", "metadata_": {"year": 2021, "genre": ["drama", "comedy"]}},
    {"title": "Outlander", "creator": "Ronald D. Moore", "metadata_": {"year": 2014, "genre": ["drama", "romance", "historical"]}},
    {"title": "Lupin", "creator": "George Kay", "metadata_": {"year": 2021, "genre": ["crime", "mystery", "thriller"]}},
    {"title": "Bridgerton", "creator": "Chris Van Dusen", "metadata_": {"year": 2020, "genre": ["drama", "romance", "historical"]}},
    {"title": "Cobra Kai", "creator": "Josh Heald", "metadata_": {"year": 2018, "genre": ["comedy", "drama", "action"]}},
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

    # --- Popular / mainstream additions (broad first-visit appeal) ---
    {"title": "The Witcher 3: Wild Hunt", "creator": "CD Projekt Red", "metadata_": {"year": 2015, "genre": ["rpg", "action"]}},
    {"title": "Minecraft", "creator": "Mojang", "metadata_": {"year": 2011, "genre": ["sandbox", "survival"]}},
    {"title": "Grand Theft Auto V", "creator": "Rockstar Games", "metadata_": {"year": 2013, "genre": ["action", "open world"]}},
    {"title": "The Legend of Zelda: Ocarina of Time", "creator": "Nintendo", "metadata_": {"year": 1998, "genre": ["action", "adventure"]}},
    {"title": "The Legend of Zelda: Tears of the Kingdom", "creator": "Nintendo", "metadata_": {"year": 2023, "genre": ["action", "adventure"]}},
    {"title": "Super Mario Odyssey", "creator": "Nintendo", "metadata_": {"year": 2017, "genre": ["platformer", "adventure"]}},
    {"title": "The Elder Scrolls V: Skyrim", "creator": "Bethesda Game Studios", "metadata_": {"year": 2011, "genre": ["rpg", "open world"]}},
    {"title": "BioShock", "creator": "Irrational Games", "metadata_": {"year": 2007, "genre": ["shooter", "science fiction"]}},
    {"title": "Half-Life 2", "creator": "Valve", "metadata_": {"year": 2004, "genre": ["shooter", "science fiction"]}},
    {"title": "Mass Effect 2", "creator": "BioWare", "metadata_": {"year": 2010, "genre": ["rpg", "science fiction"]}},
    {"title": "Persona 5", "creator": "Atlus", "metadata_": {"year": 2016, "genre": ["rpg"]}},
    {"title": "Final Fantasy X", "creator": "Square", "metadata_": {"year": 2001, "genre": ["rpg"]}},
    {"title": "Chrono Trigger", "creator": "Square", "metadata_": {"year": 1995, "genre": ["rpg"]}},
    {"title": "Undertale", "creator": "Toby Fox", "metadata_": {"year": 2015, "genre": ["rpg", "indie"]}},
    {"title": "The Legend of Zelda: The Wind Waker", "creator": "Nintendo", "metadata_": {"year": 2002, "genre": ["action", "adventure"]}},
    {"title": "Super Metroid", "creator": "Nintendo", "metadata_": {"year": 1994, "genre": ["action", "adventure"]}},
    {"title": "Metroid Prime", "creator": "Retro Studios", "metadata_": {"year": 2002, "genre": ["action", "adventure"]}},
    {"title": "Halo: Combat Evolved", "creator": "Bungie", "metadata_": {"year": 2001, "genre": ["shooter", "science fiction"]}},
    {"title": "Overwatch", "creator": "Blizzard Entertainment", "metadata_": {"year": 2016, "genre": ["shooter", "multiplayer"]}},
    {"title": "World of Warcraft", "creator": "Blizzard Entertainment", "metadata_": {"year": 2004, "genre": ["mmorpg"]}},
    {"title": "Diablo II", "creator": "Blizzard Entertainment", "metadata_": {"year": 2000, "genre": ["action rpg"]}},
    {"title": "The Sims", "creator": "Maxis", "metadata_": {"year": 2000, "genre": ["simulation"]}},
    {"title": "Pokémon Red and Blue", "creator": "Game Freak", "metadata_": {"year": 1996, "genre": ["rpg", "adventure"]}},
    {"title": "Super Mario Bros.", "creator": "Nintendo", "metadata_": {"year": 1985, "genre": ["platformer"]}},
    {"title": "Tetris", "creator": "Alexey Pajitnov", "metadata_": {"year": 1984, "genre": ["puzzle"]}},
    {"title": "Death Stranding", "creator": "Kojima Productions", "metadata_": {"year": 2019, "genre": ["action", "adventure"]}},
    {"title": "Horizon Zero Dawn", "creator": "Guerrilla Games", "metadata_": {"year": 2017, "genre": ["action rpg", "science fiction"]}},
    {"title": "Ghost of Tsushima", "creator": "Sucker Punch Productions", "metadata_": {"year": 2020, "genre": ["action", "adventure"]}},
    {"title": "Uncharted 4: A Thief's End", "creator": "Naughty Dog", "metadata_": {"year": 2016, "genre": ["action", "adventure"]}},
    {"title": "Marvel's Spider-Man", "creator": "Insomniac Games", "metadata_": {"year": 2018, "genre": ["action", "adventure", "superhero"]}},
    {"title": "Fallout: New Vegas", "creator": "Obsidian Entertainment", "metadata_": {"year": 2010, "genre": ["rpg", "post-apocalyptic"]}},
    {"title": "The Stanley Parable", "creator": "Galactic Cafe", "metadata_": {"year": 2013, "genre": ["adventure", "indie"]}},
    {"title": "Cuphead", "creator": "Studio MDHR", "metadata_": {"year": 2017, "genre": ["action", "platformer", "indie"]}},
    {"title": "Among Us", "creator": "InnerSloth", "metadata_": {"year": 2018, "genre": ["multiplayer", "party"]}},
    {"title": "Baldur's Gate 3", "creator": "Larian Studios", "metadata_": {"year": 2023, "genre": ["rpg"]}},
    {"title": "League of Legends", "creator": "Riot Games", "metadata_": {"year": 2009, "genre": ["moba", "multiplayer"]}},
    {"title": "Tomb Raider", "creator": "Crystal Dynamics", "metadata_": {"year": 2013, "genre": ["action", "adventure"]}},
    {"title": "Assassin's Creed II", "creator": "Ubisoft", "metadata_": {"year": 2009, "genre": ["action", "adventure"]}},
    {"title": "BioShock Infinite", "creator": "Irrational Games", "metadata_": {"year": 2013, "genre": ["shooter", "science fiction"]}},
    {"title": "Dishonored", "creator": "Arkane Studios", "metadata_": {"year": 2012, "genre": ["action", "stealth"]}},
    {"title": "Kingdom Hearts", "creator": "Square", "metadata_": {"year": 2002, "genre": ["action rpg"]}},
    {"title": "Metal Gear Solid 3: Snake Eater", "creator": "Konami", "metadata_": {"year": 2004, "genre": ["stealth", "action"]}},
    {"title": "God of War Ragnarök", "creator": "Santa Monica Studio", "metadata_": {"year": 2022, "genre": ["action", "adventure"]}},
    {"title": "Xenoblade Chronicles", "creator": "Monolith Soft", "metadata_": {"year": 2010, "genre": ["rpg"]}},
    {"title": "Ori and the Will of the Wisps", "creator": "Moon Studios", "metadata_": {"year": 2020, "genre": ["platformer", "adventure"]}},
    {"title": "Detroit: Become Human", "creator": "Quantic Dream", "metadata_": {"year": 2018, "genre": ["adventure", "drama", "science fiction"]}},
    {"title": "Life is Strange", "creator": "Dontnod Entertainment", "metadata_": {"year": 2015, "genre": ["adventure", "drama"]}},
    {"title": "Until Dawn", "creator": "Supermassive Games", "metadata_": {"year": 2015, "genre": ["horror", "adventure"]}},
    {"title": "Fallout 3", "creator": "Bethesda Game Studios", "metadata_": {"year": 2008, "genre": ["rpg", "post-apocalyptic"]}},
    {"title": "Donkey Kong Country", "creator": "Rare", "metadata_": {"year": 1994, "genre": ["platformer"]}},
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
