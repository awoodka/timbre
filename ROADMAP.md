# Timbre roadmap

This started as the post-MVP list in April 2026. Updated in September 2026 to show what's been built since.

## Done

- **Cross-media.** Films, shows, anime, manga and games sit alongside books in the same 31-dimension space, and recommendations cross mediums freely (`backend/tests/test_cross_media.py` checks this).
- **Natural-language search.** It works differently from the original plan: Gemini turns the request into emotions to seek and avoid, an ending tone and an optional medium, instead of embedding the query text.
- **Explanations.** "Why this fits you" is generated on demand from your closest rated works and cached. Re-ranking stayed deterministic (MMR for variety, an optional enjoyment tilt, a penalty for the wrong kind of ending) rather than an LLM pass over the top 20.
- **Batch re-analysis** when the dimensions or prompts change: `rescore.py` and `rebuild_embeddings.py`.
- **Accounts and taste.** Accounts, a saved list, a taste profile built from per-emotion ratings, taste modes, the Your Taste page, and a "you are here" marker on the Explore map.
- **Metadata** from Google Books, Open Library, TMDB, RAWG (instead of IGDB) and Jikan.
- **User-added works.** Signed-in users can add anything that's missing. Sign-ups on the live site are closed for now.

## Not done

- **Music.** The medium I most want to add next.
- **Better context for scoring.** The essay and Reddit scraper mostly comes back empty or off target (390 of 500 works got no essays), so most fingerprints rest on Gemini's own knowledge of the work.
- **Few-shot calibration.** The scoring prompt has anchor values but no scored examples, so runs can drift.
- **Score corrections.** Let people adjust a work's scores. Today's per-emotion ratings describe your reaction, not the work.
- **A text embedding** of each emotional profile stored next to the 31 scores, for richer similarity search while keeping the scores for visualization and explanations.
