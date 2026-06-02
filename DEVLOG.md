# Timbre — Development Log & Decision Journal

> **Purpose.** This is the running, nuanced context behind Timbre — the *why* behind
> choices, the concerns I'm chewing on, and exactly where I left off. The goal is that
> I (and Claude) can read this file and pick the project back up seamlessly between
> sessions.
>
> **How this differs from other docs:**
> - `ROADMAP.md` = the *what's next* feature list (big future bets).
> - `README.md` = how to run it.
> - **`DEVLOG.md` (this file)** = the *why*, the *where I left off*, decisions, concerns, and pre-roadmap ideas.

**How to use this file**
- **"Where I left off"** (next section) is the first thing to read/update each session.
- **Decisions** is append-only — record the choice, the reasoning, and the status. Don't delete; if a decision is reversed, add a new entry that supersedes it.
- **Open concerns** = unresolved worries and risks. Move to Decisions once resolved.
- **Ideas in the pot** = nuanced thoughts not yet concrete enough for the roadmap.
- **Session log** = dated narrative of what happened and what I was thinking.

---

## 📍 Where I left off  *(last updated: 2026-06-02)*

**Immediate next step:** center the 6 bipolar dims to [-0.5,+0.5] in `normalize_vector` and rebuild vectors (no re-score) — this makes the new arc dimensions actually separate recommendations. See Concerns §2b.

**State:** Full stack boots and runs locally. 50 seeded books, all analyzed.

- DB: local Postgres + pgvector in Docker (`docker compose up db`).
- Backend: runs natively (`uvicorn --reload`, :8000) — connected to local DB.
- Frontend: runs natively (`npm run dev`, :3000) — homepage + `/api` proxy verified.
- Just migrated **off AWS RDS to local Postgres** for the MVP (see Decisions §1).
- Just fixed the **cover-image host whitelist** (see Decisions §3).

**Most likely next steps (candidates, not committed):**
1. **Fix the scoring inflation in the pipeline** — revise BOTH Gemini prompts (profile → dominant-signature; scoring → "defines sustained experience" + sparsity + bipolar handling), then re-score the corpus (Concerns §2). Root cause confirmed via live experiments; this is the agreed direction over standardization.
2. **Self-host book covers** — the durable fix for the cover problem (see Concerns §1). Highest-value cleanup before any deploy.
3. Decide on a **Google Books API key** vs. switching cover source (Concerns §1).
4. Parameterize the raw SQL in `recommend.py` (Concerns §3).
5. Rename legacy `raw_claude_response` / "MediaFingerprint" leftovers (Concerns §4).

**Test status:** `tests/test_recommendations.py` = 20 pass / 15 fail. Behavioral tests green; precise-neighbor tests fail due to vector compression (Concerns §2). Failures are diagnostic — do not loosen them. Tests need `pytest` + `pytest-asyncio` (installed in the venv; not in `requirements.txt`).

---

## 🧭 Key decisions

### 1. MVP runs on local Postgres, not AWS RDS  *(2026-06-02)*
- **Decision:** Point the MVP at a local Docker Postgres. RDS connection string kept commented in `.env` for later.
- **Setup:** DB in Docker (pgvector image), backend + frontend run natively. *Not* the full `docker compose up`.
- **Why:** Easiest local loop for the MVP while still using real Postgres. Docker's macOS file-sync lag slows the edit cycle, but it's painless for a DB I never edit. "DB in a container, app on the host" is also a common real-world workflow (ties into the learning goal of industry-standard tooling).
- **Status:** ✅ Done & verified.

### 2. DB SSL is env-driven  *(2026-06-02)*
- **Decision:** TLS to Postgres is controlled by the `DB_SSL` env var (`backend/app/config.py` → `database.py`), default `false`.
- **Why:** It was previously hard-coded `ssl: False`, which is right for local Docker but would break against managed Postgres (RDS/Supabase/Neon), which require SSL. Now switching local↔hosted is a config flip (`DB_SSL=true`), not a code change.
- **Status:** ✅ Done. Was a known deferred issue; now resolved.

### 3. Cover image hosts whitelisted  *(2026-06-02)*
- **Decision:** `next.config.js` `images.remotePatterns` now allows `covers.openlibrary.org` (existing seeded data), `books.google.com`, and `books.googleusercontent.com` (newly analyzed books).
- **Why:** Covers shifted from Open Library to the Google Books API at some point, but the whitelist hadn't kept up, so `next/image` was rejecting Google Books URLs. This is a stopgap — see Concerns §1 for the real fix.
- **Status:** ✅ Done (whitelist). ⚠️ Underlying fragility remains.

### 4. Stack choices (pre-existing, recorded for context)
- **Next.js 14 App Router** (over Vite/Remix) and **FastAPI** backend — chosen partly to learn industry-standard, widely-used tooling.
- **Gemini 2.5 Flash** for emotional scoring.
- **29 emotional dimensions, intentionally media-agnostic** — so the same fingerprint extends to games/film/manga/music later (cross-media is the endgame).

### 5. Recommendation math (design rationale, recorded for context)
- **Two-step LLM pipeline:** (1) synthesize a prose *emotional profile* from gathered context (Google Books description + scraped essays + Reddit reactions), then (2) score that profile on the 29 dimensions. Separating "understand the vibe" from "score it" keeps scoring more grounded.
- **Preference vector:** ratings use midpoint 2.5. Positive ratings add the book's vector ("more of this"); negative ratings add the *complement* `1 - v` ("the opposite of this"), so a 1-star on a high-dread book actively pushes toward low-dread instead of collapsing to zero. Result is clamped ≥0 and normalized; similarity via pgvector cosine distance.
- **Why noted:** This is the conceptual heart of the product. Any change here changes what "feels similar" means.

---

## ⚠️ Open concerns

### 1. Book covers depend on flaky external origins  *(raised 2026-06-02)*
- Covers are fetched live from external hosts. **Google Books API returned HTTP 429 "quota 0/day" for anonymous access** during testing — so newly analyzed books may get *no* cover (placeholder shown; handled gracefully, doesn't crash).
- **Durable fix:** download covers once during seed/backfill and self-host (`frontend/public/covers/` or S3), storing local paths. Removes the runtime dependency on Open Library *and* Google Books and sidesteps the rate limit.
- **Open question:** get a Google Books API key, or switch cover source entirely? Self-hosting may make the source moot.

### 2. Vector discrimination is weak — a few dimensions are inflated  *(confirmed 2026-06-02 via tests)*
- **Symptom:** `tests/test_recommendations.py` = 20 pass / 15 fail. The *behavioral* tests all pass (opposites repel, dislikes push recs away, mixed prefs stay coherent), but the *precise-neighbor* tests ("X should be in Y's top 5") largely fail. The returned neighbors are still emotionally plausible — just not the exact expected book.
- **Root cause (measured across the 50-book corpus):** some dimensions have a high floor and low variance, so they stop discriminating yet dominate the (unit-normalized) cosine similarity, compressing the space:
  - `emotional_complexity`: mean **0.80**, min 0.45, stdev **0.12** — nearly constant & high → near-zero signal but always pulls vectors the same way.
  - `dread` 0.74, `melancholy` 0.70, `isolation` 0.68 also have high floors.
- **Two causes:** (a) the scoring prompt asks for sparsity ("3-6 dims above 0.5, many near 0-0.3") but the model isn't honoring it for the structural dims; (b) the seed corpus is genuinely dark-skewed (2× McCarthy, Beloved, Bell Jar, No Longer Human, A Little Life…), so some high dread/melancholy is real.
- **Per-book profiles themselves are accurate** — e.g. The Road = dread/grief/isolation, Cerulean Sea = warmth/hope/joy, Blood Meridian = dread/vastness/isolation. The issue is the *distribution across books*, not individual scoring quality.
- **ROOT CAUSE CONFIRMED (2026-06-02, via live Gemini re-score experiments): it's the PROMPTS, in both Gemini calls — not a math problem.**
  - **Call #1 (profile)** asks the model to *narrate the full emotional arc* ("how tone shifts," "specific moments"). For broad-arc books this enumerates every fleeting emotion, which the scorer then rewards. *This is the dominant cause for wide-range books.*
  - **Call #2 (scoring)** scale is framed as "0 = absent, 1 = dominant," so anything *mentioned* gets a mid score. And the 4 structural/bipolar dims (emotional_complexity, pacing, predictability, catharsis) are scored with presence/absence framing, so e.g. `emotional_complexity` never scores low.
- **Experiment evidence (dims ≥0.5, old → new):** revised *scoring* prompt alone: The Road 13→8, Cerulean Sea 10→8 (focused books sharpen), but **The Hobbit stayed 19→19**. Revised *profile* prompt ("dominant signature") + revised scoring: **The Hobbit 19→9 and emotionally correct** (dread 0.75→0.30, tension 0.80→0.30, emotional_complexity 0.85→0.40; wonder/warmth/nostalgia/hope now dominate). Both stages are needed.
- **DECISION: fix upstream in the pipeline (revise both prompts), not via standardization.** Rationale: the bad scores were *wrong* (cozy book scored dread 0.75), not merely unscaled — fixing the prompts makes scores correct and improves all future books. Standardization remains a *complementary* option if precision still lags after re-scoring; no longer the primary lever.
- **Implementation TODO (not yet done):** (1) rewrite `generate_emotional_profile` prompt → dominant-signature, not full-arc; (2) rewrite `score_emotional_dimensions` prompt → "defines the sustained experience" scale + anchors + sparsity cap + separate bipolar handling for the 4 structural dims; (3) re-analyze the 50-book corpus (NOTE: profiles are context-grounded, so a true re-score re-gathers context → slow + hits the flaky DDG/Reddit/Google Books path; budget for it); (4) re-run tests and compare. Throwaway experiment scripts live at `/tmp/rescore_experiment.py` and `/tmp/profile_experiment.py`.
- **Note:** the failing tests are kept as-is — they're diagnostic signal, NOT to be loosened to force green.

### 2b. v2 re-score done — arc captured in SCORES, but washed out in the VECTOR  *(2026-06-02)*
- **Implemented:** added 2 arc dims (`emotional_trajectory`, `ending_valence`; NUM_DIMENSIONS 29→31), revised both prompts (dominant-signature profile + dominance/sparsity/bipolar scoring), migrated the pgvector column to vector(31), and re-scored all 50 books via `rescore.py` (distills the existing profile — no re-scraping; backup written to `backend/rescore_backup_*.json`). 50/50 succeeded. Tests 20→22 pass.
- **Win:** arc dims have full 0–1 spread and correctly separate same-emotion/different-ending works at the score level (A Little Life: trajectory 0.00 / ending_valence 0.25 / catharsis 0.10 vs The Book Thief: 0.10 / 0.50 / 0.30). Inflation down modestly (emotional_complexity 0.80→0.67).
- **Catch (confirmed with data):** the arc info does NOT yet move similarity — cosine(A Little Life, The Book Thief)=0.878 — because the bipolar dims sit in [0,1], so a "descends" score of 0.0 contributes nothing instead of pointing opposite to "rises." Shared grief/melancholy dims dominate the magnitude.
- **NEXT (agreed direction): center the 6 bipolar dims to [-0.5,+0.5] in `normalize_vector`.** Semantic transform (axis centered at its neutral midpoint), NOT corpus standardization. No re-score needed — just rebuild vectors from stored scores. This is what makes arc actually separate recommendations.

### 3. Raw SQL string interpolation in `recommend.py`
- `rated_ids` are interpolated directly into the query string rather than parameterized. Currently the values are server-generated UUIDs (not user free-text), so not exploitable today — but it's a pattern to clean up before any user-supplied data reaches it.

### 4. Legacy naming leftovers
- DB column `raw_claude_response` and the FastAPI app title "MediaFingerprint" predate the switch to Gemini / the "Timbre" name. Cosmetic but misleading. Rename when convenient (column rename needs a migration).

### 5. Frontend dependency vulnerabilities
- `npm install` reports 5 vulnerabilities (1 moderate, 4 high). Not blocking locally; run `npm audit` and address before deploy.

---

## 💡 Ideas in the pot  *(nuanced / pre-roadmap thinking)*

*(These overlap with `ROADMAP.md` but capture the reasoning, not just the feature name. Add half-formed thoughts here freely.)*

- **Dual embeddings.** Keep the 29-dim interpretable fingerprint for explainability/visualization, but *also* store a high-dim text embedding of the emotional profile for richer similarity. Open question: which drives retrieval, and how to blend them.
- **Agentic re-ranking.** Retrieve ~20 by vector similarity, then have an LLM pick the best 5 and *explain* the match in natural language ("a shared kind of loneliness — surrounded by people who don't understand you"). The explanation may be as valuable as the ranking.
- **Natural-language emotional queries.** "Something that feels like a warm bath after a long day" → embed the query against profiles. Depends on dual embeddings.
- **Personal emotional taste profiles.** Aggregate a user's rating history into an average fingerprint — both for better recs and as a "this is your emotional taste" visualization.
- **Cross-media (the endgame).** Books are just medium #1. The 29 dimensions are media-agnostic on purpose. Validate they hold up across games/film/manga/music before committing to the cross-media promise.

---

## 📓 Session log

### 2026-06-02
- **Goal:** make the DB local for the MVP (was pointed at AWS RDS) and make local dev easier.
- Talked through Docker vs. native trade-offs; landed on **DB-in-Docker + app-native** (Decision §1). Key insight: Docker's value is uneven — huge for Postgres/pgvector (painful to install natively, never edited), costly for the app (macOS file-sync lag slows hot reload).
- Made **DB SSL env-driven** (Decision §2) — resolved a long-standing deferred issue and made the local↔RDS switch a config flip.
- Switched `.env` to local Postgres; kept RDS commented for the expansion phase.
- Added `README.md` with run steps; removed the obsolete `version:` key from `docker-compose.yml`.
- **Discovered & fixed** the cover-image whitelist mismatch (Decision §3). While testing, **found the Google Books API is rate-limited to 0/day anonymously** (Concern §1) — covers for new books will be empty until self-hosted or keyed.
- Booted the full stack locally and verified end-to-end (DB healthy, backend 50 analyzed books, frontend serving + proxying). Had to re-run `npm install` (incomplete `node_modules`, missing `next` binary).
- Created this DEVLOG.
- **Ran the recommendation/vector tests** (`tests/test_recommendations.py`): 20 pass / 15 fail. Fixed the test's hard-coded SSL to use env-driven `DB_SSL` (so it runs against local Postgres); installed `pytest`/`pytest-asyncio` into the venv. **Finding:** vectors are individually accurate and behaviorally sound, but a few inflated dimensions (esp. `emotional_complexity`, mean 0.80 / stdev 0.12) compress the space and hurt precise-neighbor ranking → Concerns §2. Next session candidate: mean-center dimensions before building vectors.

<!--
Template for future entries:

### YYYY-MM-DD
- **Goal:** what I set out to do this session.
- **Did:** what actually changed.
- **Decided:** any choices (also add to Key decisions).
- **Concerns / open questions:** what I'm unsure about (also add to Open concerns).
- **Left off at:** update the "Where I left off" section at the top too.
-->
