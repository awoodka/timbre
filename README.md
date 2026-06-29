# Timbre

Find your next book, film, game, or show by how it makes you *feel* — not by genre.

Most recommendation engines sort culture into bins. If you liked one space opera, here are nine more space operas. But genre is a filing system, not a feeling. It tells you a book has spaceships in it; it tells you nothing about whether reading it will leave you exhilarated, or hollowed-out, or quietly at peace. Two horror novels can sit on the same shelf and do completely opposite things to you. A literary novel and a video game can do exactly the same thing.

Timbre is built on a simple bet: the thing you're actually chasing when you love a story isn't its genre or even its medium — it's the emotional texture it leaves behind. The held breath of real suspense. The specific ache of nostalgia for a place you've never been. The warmth of a story that feels like being looked after. If you can describe *that*, you can find more of it anywhere — in a manga, a film, a game, a novel.

So Timbre throws out the categories and maps everything into one shared emotional space.

## How it works

Every work is read by a language model (Gemini) and scored across **31 emotional dimensions** — roughly two dozen *felt* emotions (isolation, wonder, dread, warmth, grief, awe, tenderness…) plus a handful of structural axes for the *shape* of the experience: how fast it moves, whether it resolves or leaves you raw, whether it climbs toward light or sinks into the dark, how it lands at the end.

That turns each book, film, or game into a single point in the same 31-dimensional space — a kind of emotional fingerprint. And once everything lives in one space, "what feels like this?" stops being a matter of taste and becomes a measurable question: find the nearest points, regardless of medium. A novel and a game that land close together genuinely *feel* alike, even though nothing on their surface — words on a page versus a controller in your hands — has anything in common.

That's the whole idea. Everything else is making it something you can actually use.

## What you can do with it

- **Rate things, and get a taste that's actually yours.** As you tell Timbre what landed for you, it learns the emotional center of gravity of your taste — and instead of flattening you into one "type," it notices that most people contain a few different moods. It splits your taste into a small number of **modes** (the quiet, melancholy you; the one who just wants to be thrilled) and recommends honestly for each, so your comfort-watch night and your edge-of-the-seat night don't get averaged into mush.
- **Describe a feeling in plain words.** Type *"something tense and lonely that ends on a little bit of hope"* and Timbre reads it into the same emotional space and hands back works that match — across every medium.
- **Compose a mood by hand.** Turn up the feelings you want, turn down the ones you don't, and watch the recommendations move in real time.
- **Ask why.** Any recommendation can explain itself — a short, specific note on *why this fits you*, written on the spot from the works you've loved and the emotional thread that connects them to it. "Why this fits you," not "people who bought X also bought Y."
- **See the whole map.** A 3D view of the entire collection, laid out so that works near each other feel alike, with a *you are here* marker for your own taste. You can see the neighborhoods of feeling and where you live in them.
- **Read your fingerprint.** A page that turns your ratings into a portrait — the emotions you're drawn to, the ones you steer around, and the shape of what moves you.

## Where this actually is

This is a working prototype, not a finished product. I'm building it to the point where I can hand it to friends and have it feel real.

The collection right now is **300 works, hand-seeded — 50 each across books, films, shows, anime, manga, and games.** Small enough that I trust what's in it; big enough that the cross-media matching has something to say. Music is what I most want to add next: it's the purest test of the whole premise, since a song has no plot to fall back on — only feeling.

The honest caveats: every work's emotional fingerprint comes from a single model pass, so the scores are interpretations, not measurements, and the recommendations are only as sharp as that read on a corpus this small. I'd rather ship something transparent about how it thinks than something that hides a black box behind a star rating.

## Built with

- **Frontend** — Next.js (App Router): the catalogue, the 3D explorer, the recommendation feed, accounts, dark mode.
- **Backend** — FastAPI (async), with Gemini doing the emotional scoring, the natural-language search, and the explanations.
- **Data** — Postgres + pgvector, which does the nearest-neighbor search over the emotional fingerprints right in the database.

## Running it

Everything runs as one Docker Compose stack — Postgres, the API, and the web app together:

```bash
cp .env.example .env     # then add your GEMINI_API_KEY (and a SECRET_KEY)
make up                  # db + backend + frontend, hot-reloading
```

The app comes up at http://localhost:3000. To load the starter collection and score it (needs a valid `GEMINI_API_KEY`):

```bash
docker compose exec backend python -m seed --analyze
```

`make rebuild` picks up dependency changes, `make logs` tails everything, and `make down` stops the stack (your data persists). There's a hardened `make prod` path as well, meant to go online behind a Cloudflare Tunnel.
