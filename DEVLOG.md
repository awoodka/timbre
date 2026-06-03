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

**Immediate next step:** film is DONE and the cross-media thesis is validated (§4c). Candidate next moves: (a) add the next medium — **TV via TMDB** (nearly identical to film; mind the series/season unit) — then anime/manga, games, music per the roadmap; (b) the now-larger 100-item corpus may be enough to revisit the parked book-scoring issues (Concerns §3) — re-run the suite and judge. Decide based on whether breadth (more media) or quality (tuning) matters more next.

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

### 4b. Generalized the foundation: Book → MediaItem (cross-media groundwork)  *(2026-06-02)*
- **Why:** the 31-dim fingerprint was always meant to be media-agnostic; this makes adding a medium a plug-in, not a rewrite — done BEFORE implementing any new medium so each one lands cleanly.
- **Data model:** `Book` → `MediaItem` (table `books` → `media`); `author`→`creator`, `isbn`→`external_id`, `raw_claude_response`→`raw_response`, new `medium` field (default 'book'). One-time idempotent migration `backend/migrate_to_media.py` renamed in place — 50 rows + their LLM vectors preserved (verified 50→50).
- **Context sources are now a per-medium adapter:** `app/services/sources/` — `__init__.gather_context(medium, title, creator)` + `MEDIUM_NOUNS` + a `_METADATA_FETCHERS` registry; `book.py` is the Google Books fetcher; `web.py` is the shared (medium-aware) essay+Reddit scraper. **To add a medium: write one `fetch_metadata` and register it.**
- **Pipeline/API generalized:** `analyze_book`→`analyze_media(medium, …)` (prompts use the medium noun + "creator"/"audience"); router `/api/books`→`/api/media`; schemas `Media{Create,Response,SimilarResponse}` (wrapper field `book`→`item`); `RatingInput.book_id`→`media_id`. Frontend points at `/api/media`, uses `creator`, aliases `{item}`→`book` in JSX so the UI was untouched (still book-flavored copy for now).
- **Verified behavior-preserving:** test suite returns the identical 64/6; `/api/media`, `/similar`, `/recommend` all work; frontend hot-reloaded clean.

### 4c. Film implemented — cross-media thesis VALIDATED  *(2026-06-02)*
- **Shipped (shared pipeline, no separate one):** `app/services/sources/film.py` (TMDB `fetch_metadata` with remake disambiguation by director — needed: "Solaris" returns the 2002 remake at higher popularity than Tarkovsky's 1972); registered `"film"` in `_METADATA_FETCHERS`; `tmdb_api_key` in config/.env; `image.tmdb.org` whitelisted; 50 canonical+diverse `SEED_FILMS` (dedup by `(medium,title)` so film adaptations aren't skipped by namesake books); §6 craft hint in the profile prompt (visual media factor cinematography/color/score — confirmed working). **Bug fixed:** `seed`/`_run_analysis` never persisted `cover_image_url` from the analysis result (books were masked by the Open Library backfill); now saved.
- **Seeded + analyzed all 50 films, 0 failures.** Corpus is now 100 items (50 books + 50 films) standardized in ONE shared space.
- **Cross-media validation (the thesis test):** 8/10 novel↔film pairs land clearly nearer their source novel than an emotionally-opposite book — Gone Girl film↔novel 0.85, Never Let Me Go 0.85, The Shining 0.69, Solaris 0.69, Annihilation 0.60, Rebecca 0.61, The Book Thief 0.56, The Road 0.48 — while film↔Hobbit is strongly negative. The medium-dominates failure mode did NOT occur. Live rec: rate *The Shining* (film) → returns The Thing/Alien (films) + Haunting of Hill House/Mexican Gothic + The Shining (book). Cross-media recommendation works.
- **Informative outliers:** The Great Gatsby film↔novel ≈ 0 (Luhrmann's maximalist spectacle genuinely feels unlike the wistful novel — the engine correctly detected adaptation divergence, NOT a bug); The Book Thief a near-tie (straddles grief/warmth).
- **Film test suite (2026-06-02):** mirrored the book suite for films — film ground truth in `_helpers.py` (FILM_CLUSTERS / FILM_ARC_* / FILM_EXPECTED_*, source-grounded), a `film_corpus` fixture, and `test_film_{geometry,similarity,arc,dimensions,recommendation}.py`. **70 pass / 4 fail**; the 4 are diagnostics (Annihilation reads as awe>cosmic-horror so it's nearer 2001 than The Thing; Solaris's dread edges it toward horror over Her; Manchester by the Sea ending_valence 0.40 just above the tragic bar; sparsity inflation in Arrival/Little Women/Interstellar/Her/Spirited Away). Whole suite now **143 pass / 9 fail** (5 book + 4 film diagnostics, 0 cross-media). These join the parked tuning list (Concerns §3).
- **Tests: 73 pass / 5 fail.** New `test_cross_media.py` fully green. The previously-orphaned *The Year of Magical Thinking* now PASSES — adding films re-centered the space and gave it a real neighbor (more data helps, as predicted). The 5 remaining failures are the same parked book-scoring issues (Concerns §3). `conftest` now exposes `corpus` (books, by title) + `media_corpus` (all, by `(medium,title)`) to handle book/film title collisions.

### 5. Recommendation math (design rationale, recorded for context)
- **Two-step LLM pipeline:** (1) synthesize a prose *emotional profile* from gathered context (Google Books description + scraped essays + Reddit reactions), then (2) score that profile on the 29 dimensions. Separating "understand the vibe" from "score it" keeps scoring more grounded.
- **Preference vector:** ratings use midpoint 2.5. Positive ratings add the book's vector ("more of this"); negative ratings add the *complement* `1 - v` ("the opposite of this"), so a 1-star on a high-dread book actively pushes toward low-dread instead of collapsing to zero. Result is clamped ≥0 and normalized; similarity via pgvector cosine distance.
- **Why noted:** This is the conceptual heart of the product. Any change here changes what "feels similar" means.

---

### 6. Cross-media vector space = shared felt core (approach #1)  *(2026-06-02)*
- **Decision:** all media embed into ONE shared, medium-agnostic vector (the current felt/structural dims, possibly + universal felt emotions like disgust/beauty/flow). Medium-specific aesthetic channels (color, score, panel layout, agency, tempo…) are NOT dimensions — they are INPUTS the LLM uses when scoring the shared felt dims (a cold, drone-scored film simply scores higher `dread`).
- **Why:** cross-media recommendation ("this game feels like Norwegian Wood") is the killer feature and needs every medium in one space. **Rejected alternative — zero-pad medium-specific dims (N/A → 0):** under cosine + standardization it makes *medium* the dominant signal and collapses cross-media similarity. The padded blocks act like a one-hot medium tag (a book can never match a film's color dims, so cross-media cosine is strictly deflated by `|shared|/|total|`); and mean-centering turns each medium's zero-block into a shared per-medium offset that clusters items by medium. It also re-introduces the 0≠absent bug for bipolar aesthetic axes (0 = "maximally cool", not "N/A"). Don't revisit zero-padding.
- **Status:** adopting for film (first medium). Aesthetic richness is preserved via the LLM scoring inputs now, and a future dual-vector later (see Ideas).

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
- **NEXT (originally): center the 6 bipolar dims.** SUPERSEDED by §2c — see below.

### 2c. Measured the embeddings — STANDARDIZATION is the real lever, not bipolar centering  *(2026-06-02)*
- **Tested three transforms on the live v2 vectors** (mean pairwise cosine across all 50 books; lower = better spread):
  - raw [0,1]: **0.693**, despair pair (A Little Life ↔ The Book Thief) = 0.878
  - bipolar-centered only (subtract 0.5 from the 6 axes): **0.638**, despair pair = 0.865 — *barely moves the needle*
  - standardized (mean-center ALL dims): **−0.016**, despair pair = **0.507** (and A Little Life ↔ The Road 0.348, Book Thief ↔ Road 0.052) — *decisive*
- **Why:** all vectors sit in the non-negative orthant with a shared dark baseline (melancholy 0.70, dread 0.68, emotional_complexity 0.67 across the corpus), which dominates cosine. Subtracting the per-dimension mean removes that shared "everyone is dark" mass so similarity is driven by what DISTINGUISHES books. Mean-centering all dims also centers the bipolar ones, so it **subsumes** bipolar centering — don't do both.
- **CORRECTION to §2b:** bipolar centering alone is nearly cosmetic here; the prompt fix made the arc *scores* correct but didn't fix the *geometry*. Standardization fixes the geometry.
- **DECISION: standardize in vector construction.** Store a corpus **centroid** (mean vector); build `emotion_vector = normalize(scores − centroid)`. No re-score needed — rebuild from stored `emotion_breakdown`. Trade-off: corpus-dependent — recompute the centroid on each full re-score; re-standardize periodically as the (cross-media) library grows. Optional refinement: z-score (also ÷ per-dim stdev) so high-variance dims don't dominate; mean-centering alone already works.
- **Keep raw scores for display:** `emotion_breakdown` stays the human-readable [0,1] profile; only `emotion_vector` is standardized.
- **DONE (2026-06-02): standardization implemented and integrated into the pipeline.**
  - `emotional_analysis.py`: added `compute_centroid()` + `standardize_vector()`; `normalize_vector()` kept as the provisional (pre-standardization) vector.
  - New `app/services/embeddings.py: recompute_all_embeddings(session)` — recomputes the centroid from the current corpus and rebuilds every `emotion_vector = normalize(scores − centroid)`. Pure arithmetic, no LLM calls.
  - Pipeline: `books._run_analysis` calls it after every analyze/reanalyze; `rescore.py` calls it at the end; `rebuild_embeddings.py` added for on-demand rebuilds. So the whole corpus is always in one consistent mean-centered space.
  - `recommend.build_preference_vector` rewritten for centered space: signed weighted sum `Σ vec·(rating−2.5)`, normalized — dropped the old `1−vec` complement and non-negative clamp (artifacts of [0,1] vectors).
  - **Result on live data:** despair pair 0.878→0.507; `/recommend` on dark inputs returns a coherent dark/grief set (All Quiet 0.61, The Shining, 1984, Never Let Me Go). Tests 22→21 — see "Where I left off"; the suite now encodes the OLD geometry and needs rewriting, NOT the model.
  - **Scaling caveat:** re-standardizing the whole corpus on every single add is fine now; for a large/cross-media library, optimize (freeze centroid, batch). Optional refinement still open: z-score (÷ per-dim stdev) so high-variance dims don't dominate.

### 3. Raw SQL string interpolation in `recommend.py`
- `rated_ids` are interpolated directly into the query string rather than parameterized. Currently the values are server-generated UUIDs (not user free-text), so not exploitable today — but it's a pattern to clean up before any user-supplied data reaches it.

### 4. Legacy naming leftovers
- DB column `raw_claude_response` and the FastAPI app title "MediaFingerprint" predate the switch to Gemini / the "Timbre" name. Cosmetic but misleading. Rename when convenient (column rename needs a migration).

### 5. Frontend dependency vulnerabilities
- `npm install` reports 5 vulnerabilities (1 moderate, 4 high). Not blocking locally; run `npm audit` and address before deploy.

---

### 3. Test suite rebuilt as a diagnostic instrument — and the issues it reveals  *(2026-06-02)*
- **Why the old suite was weak:** `test_recommendations.py` asserted brittle *absolute top-k* membership ("book X must be in book Y's top 5" out of 50) with hand-picked, un-sourced expectations, no test of geometry/standardization, and nothing testing the arc dimensions. It conflated scoring quality with embedding geometry and broke whenever the model changed (not because the model got worse).
- **New suite** (`backend/tests/`, source-grounded ground truth + citations in `_helpers.py`): `test_geometry.py` (shape, finiteness, unit-norm, discrimination/no-narrow-cone, no dead dims), `test_emotional_similarity.py` (RELATIVE cluster cohesion/separation + ordered triplets, emotion-over-genre, incl. adversarial probes), `test_arc_discrimination.py` (ending_valence vs sourced tragic/uplifting labels, arc separates same-emotion works), `test_recommendation_behavior.py` (preference-vector behavior, cluster-based), `test_dimension_validity.py` (per-book dominant/absent emotions vs consensus, sparsity). Loads the corpus once via a `corpus` fixture. **64 pass / 6 fail** — failures are intentional (the algorithm's to-do list, NOT tests to loosen).
- **DECISION (2026-06-02): NOT fixing these yet.** The 50-book seed is too small/dark-skewed to tune against without overfitting; revisit once the corpus grows. Suite stays as a diagnostic baseline.
- **Algorithm issues the suite reveals (to revisit after the corpus grows):**
  1. **Specific mis-scorings.** `No Longer Human` is over-scored on dread/gothic → it's *negatively* correlated with `Norwegian Wood` (−0.16) yet 0.81 with `Rebecca`, contradicting sourced kinship. `The Year of Magical Thinking` is an orphan (best neighbor only 0.30) — likely scored on obsession/confusion instead of grief. `Flowers for Algernon` ending_valence 0.40 is too soft for a consensus-devastating ending.
  2. **Residual scoring inflation.** `Beloved` (15), `Fahrenheit 451` (17), `The Secret History` (13), `The Left Hand of Darkness` (13) light up >12 dims ≥0.5 — the prompt fix reduced inflation corpus-wide but not for these.
  3. **Arc/structural dims can over-join emotionally-different works.** `Beloved`↔`Fahrenheit 451` (0.60) is driven by shared high trajectory/catharsis, not shared emotion. Worth considering a modest down-weight of structural dims, or revisiting their scoring.

## 💡 Ideas in the pot  *(nuanced / pre-roadmap thinking)*

*(These overlap with `ROADMAP.md` but capture the reasoning, not just the feature name. Add half-formed thoughts here freely.)*

- **Dual embeddings.** Keep the 29-dim interpretable fingerprint for explainability/visualization, but *also* store a high-dim text embedding of the emotional profile for richer similarity. Open question: which drives retrieval, and how to blend them.
- **Agentic re-ranking.** Retrieve ~20 by vector similarity, then have an LLM pick the best 5 and *explain* the match in natural language ("a shared kind of loneliness — surrounded by people who don't understand you"). The explanation may be as valuable as the ranking.
- **Natural-language emotional queries.** "Something that feels like a warm bath after a long day" → embed the query against profiles. Depends on dual embeddings.
- **Personal emotional taste profiles.** Aggregate a user's rating history into an average fingerprint — both for better recs and as a "this is your emotional taste" visualization.
- **Cross-media (the endgame).** Books are just medium #1. The dimensions are media-agnostic on purpose. Validate they hold up across games/film/manga/music before committing to the cross-media promise.

### Cross-media implementation roadmap  *(agreed 2026-06-02)*
Implement each medium independently, **least → most difficult** (difficulty driven by: clean metadata API? self-contained unit? narrative-arc fit? experience variance?):
1. **Film** — TMDB; clean unit, perfect arc fit. FIRST.
2. **TV shows** — TMDB; series/season unit problem, long arcs.
3. **Anime / Manga** — AniList/Jikan; best emotional discourse online; long-series unit problem.
4. **Video games** — RAWG/IGDB; agency + runtime variance + mechanical (non-text) emotion.
5. **Music** — Spotify (valence/energy audio features!)/MusicBrainz/Genius; mood-only, non-narrative — the conceptual frontier, LAST.
The big divide: narrative media (film/TV/anime/manga/games) fit the arc model; mood-only media (music) don't.

### Medium-specific emotional dimensions — brainstorm  *(2026-06-02; integration into one vector space is the NEXT problem, deliberately not solved yet)*
Key reframe — the "new dimensions" a medium adds are TWO different kinds:
- **(A) Universal felt emotions the book-only seed under-sampled** — e.g. disgust/revulsion, aesthetic beauty, flow/absorption, groove/bodily-pleasure, startle (acute fear-spike vs slow dread), frustration, earned-mastery, camaraderie. A book CAN evoke these; adding them keeps ONE shared space, just richer.
- **(B) Medium-bound aesthetic/sensory channels** — genuinely undefined for some media (a book has no color value). These are the hard part of the single-space problem.
Per-medium (B) channels: **Film/TV** color temperature/saturation/luminance, image texture, shot intimacy, camera kineticism, score prominence, sonic density/silence, spectacle (+ TV: serialized investment, episodic rhythm). **Anime** + visual expressionism/exaggeration, symbolic color. **Manga/comics** ink/tonal heaviness, line energy, panel rhythm, negative space ("ma"), stylization (no sound/motion, mostly B&W). **Games** agency/control, challenge/mastery/flow, immersion/presence, compulsion/reward-loop, exploratory freedom, consequence/choice-weight (+ film's audio/visual). **Music** tempo, energy, valence, danceability/groove, acousticness/timbre, loudness/dynamics, dissonance, production density — many measurable via Spotify; structural/sonic-arc dims (pacing→tempo, catharsis→build/drop) port, narrative dims don't.
Judgment that matters: aesthetic channels mostly FEED the existing 31 felt dims (a desaturated film already scores high dread). Their marginal value is WITHIN-medium discrimination (two cozy films, warm-lit vs cold-lit, should differ). Decide per dimension whether that discrimination is worth breaking the shared space.

### Incorporating medium-specific aesthetics later (DEFERRED — keep, don't lose)
Decision §6 starts with the shared felt core only (aesthetics feed the LLM scoring, not separate dims). These richer approaches are deliberately parked for when WITHIN-medium discrimination matters — they're how Timbre eventually captures what makes each medium unique (color/music in film, timbre/groove in music, agency in games — see the dimension brainstorm above). Do NOT lose these:
- **Primary path — DUAL-VECTOR** (generalizes the roadmap's dual-embedding): each `MediaItem` keeps the shared emotional vector (used for ALL cross-media similarity/recs) PLUS an optional, nullable **`aesthetic_vector`** holding medium-specific channels (film: color temp/saturation/luminance + score prominence; music: tempo/energy/valence/danceability/timbre — many free from Spotify audio features; games: agency/challenge/immersion). Cross-media queries use the shared vector; within-medium queries blend or re-rank with the aesthetic vector. **Additive on the current foundation:** a nullable `aesthetic_vector` column + a small per-medium aesthetic-dimension registry; no change to the shared space. Pairs naturally with agentic re-ranking (shared core retrieves → aesthetic vector / LLM re-ranks + explains).
- **Other options considered:** masked / medium-aware similarity (compare only dims applicable to BOTH items); neutral-imputation (set N/A dims to the axis neutral/mean, not 0 — kills the 0≠absent bug but only partially fixes medium-dominance).
- **Trigger to revisit:** when two works that match on felt-emotion but differ aesthetically feel wrongly identical, OR when adding **music** (Spotify audio features are a ready-made aesthetic vector and a natural first dual-vector medium).

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
