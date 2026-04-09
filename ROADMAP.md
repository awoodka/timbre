# Timbre — Post-MVP Roadmap

Ideas and enhancements to implement once the MVP is stable and validated.

---

## Retrieval & Similarity

- **Dual embedding architecture**: Store a high-dimensional text embedding (768/1536-dim from an embedding model) of each emotional profile description alongside the 25 interpretable dimension scores. Use the text embedding for richer similarity search, keep the 25-dimension fingerprint for visualization and explainability.

- **Agentic re-ranking**: After retrieving the top ~20 candidates via embedding similarity, pass them through an LLM to reason about which 5 are the best matches and generate natural language explanations ("these share a specific kind of loneliness — being surrounded by people who don't understand you").

- **Natural language queries**: Let users describe what they want emotionally ("something that feels like a warm bath after a long day") and embed that query against the emotional profile embeddings.

## Cross-Media Expansion (Phase 2)

- Add support for games, film, manga, music
- The 25 emotional dimensions are already media-agnostic — validate they work across types
- Cross-media recommendations: "this game feels like reading Norwegian Wood"

## Analysis Pipeline

- Few-shot calibration: include scored examples in the LLM prompt so scoring is more consistent across runs
- User-submitted emotional corrections: let users adjust scores, building a feedback loop
- Batch re-analysis when dimensions change

## Social / Personalization

- User accounts and saved libraries
- Personal emotional preference profiles built from rating history
- "Emotional taste" visualization — your average fingerprint across rated media

## Data

- Integrate external metadata APIs (Open Library, IGDB, TMDB) for cover art, descriptions, etc.
- Community-contributed media entries
