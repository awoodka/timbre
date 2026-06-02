# Timbre

An emotional recommendation engine. Books are scored on 29 interpretable,
media-agnostic emotional dimensions (isolation, wonder, dread, warmth, …) and
recommended by emotional similarity rather than genre. Books are the first
medium; the goal is cross-media ("this game feels like reading *Norwegian Wood*").

## Stack

- **Frontend** — Next.js 14 (App Router, JSX), recharts. Port `3000`.
- **Backend** — FastAPI + async SQLAlchemy + asyncpg. Gemini 2.5 Flash for scoring. Port `8000`.
- **Database** — Postgres 16 + pgvector. Port `5432`.

## Local development (MVP setup)

The database runs in Docker (so pgvector "just works"); the backend and frontend
run natively for fast hot-reload.

### 1. Start Postgres

```bash
docker compose up db          # Postgres 16 + pgvector on :5432
```

This is the only container you need for day-to-day work. Connection settings
live in `.env` (copy from `.env.example` if you don't have one) — by default it
points at this local DB with SSL off.

### 2. Run the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000
```

Seed ~50 books (optional `--analyze` runs the Gemini scoring pipeline; needs a
valid `GEMINI_API_KEY` and the DB running):

```bash
python -m seed              # insert books only
python -m seed --analyze    # insert + emotional analysis
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev                            # http://localhost:3000
```

The frontend proxies `/api/*` to `http://localhost:8000` (override with
`API_TARGET`).

## Configuration

| Env var          | Purpose                                        | Local default |
|------------------|------------------------------------------------|---------------|
| `DATABASE_URL`   | asyncpg connection string                      | local Docker DB |
| `DB_SSL`         | TLS to Postgres — `true` for managed DBs (RDS/Supabase/Neon) | `false` |
| `GEMINI_API_KEY` | Google Gemini key for emotional analysis       | — |

To point at a hosted Postgres later, swap `DATABASE_URL` and set `DB_SSL=true`.
No code changes needed.

## Running the whole stack in Docker (optional)

```bash
docker compose up           # db + backend + frontend
```

Slower iteration (container file-sync lag on macOS), but a single command and a
fully pinned environment — closest to production.
