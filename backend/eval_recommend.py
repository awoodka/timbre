"""Offline evaluation of the recommendation engine — a re-runnable report card.

Runs synthetic "personas" with KNOWN tastes through the REAL algorithm
(`cluster_taste_modes` + `mmr_rerank` + cosine retrieval) against the REAL corpus,
and prints interpretable metrics focused on:

  • on-target match  — do a mode's recs score high on the emotions it's about,
                       vs. the corpus baseline (lift)?
  • mode recovery    — does a genuinely split taste produce the right number of
                       modes, each labeled with the right emotions?
  • multi-modal value — for a split taste, how much sharper are the per-mode recs
                       than today's single averaged-vector recs?

What this CAN tell you: the algorithm does the right thing GIVEN the emotion vectors.
What it CANNOT: whether the vectors themselves are faithful, or whether a human finds
the recs delightful — that needs eyeballing now + real-user feedback later.

Run:  docker exec timbre-backend-1 sh -c "cd /app && python eval_recommend.py"
"""

import asyncio

import numpy as np
from sqlalchemy import select

from app.database import async_session
from app.dimensions import FELT_KEYS
from app.models.media import MediaItem
from app.services.taste_modes import cluster_taste_modes, mmr_rerank

N_LOVED = 6   # exemplar "loved" works per sub-taste (a persona's rating history)
POOL = 30     # candidates retrieved before MMR (matches the endpoint)
LIMIT = 12    # final recs per mode (matches the endpoint)

# Each persona = a list of sub-tastes; one sub-taste = single-modal, two = a SPLIT
# taste that SHOULD surface two modes. Keys are the emotions that define the taste.
PERSONAS = {
    "Dread-lover":              [("dread", "tension", "isolation")],
    "Warmth-lover":             [("warmth", "serenity", "intimacy")],
    "Wonder-seeker":            [("wonder", "vastness", "hope")],
    "Split · dread + warmth":   [("dread", "tension", "isolation"), ("warmth", "serenity", "intimacy")],
    "Split · wonder + grief":   [("wonder", "vastness", "hope"), ("grief", "melancholy", "nostalgia")],
}


def _unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def _emo(bd, keys):
    """Mean raw score over the given emotion keys for one work."""
    return float(np.mean([bd.get(k, 0.0) for k in keys])) if keys else 0.0


def _on_target(recs, keys):
    """Mean on-target emotion intensity across a set of recs."""
    return float(np.mean([_emo(r["bd"], keys) for r in recs])) if recs else 0.0


def mode_label_emotions(members, n=3):
    """The mode's defining emotions = top felt dims of the cluster's mean breakdown
    (mirrors recommend._mode_emotions)."""
    sums = {}
    for c in members:
        for k, v in (c["bd"] or {}).items():
            if k in FELT_KEYS:
                sums[k] = sums.get(k, 0.0) + v
    ranked = sorted(sums, key=lambda k: -sums[k])
    return [k for k in ranked[:n] if sums[k] / len(members) >= 0.4]


def retrieve(corpus, centroid, exclude_ids, k):
    """The k corpus works nearest `centroid` by cosine (excludes the loved set) —
    the numpy equivalent of the endpoint's pgvector `<=>` retrieval (unit-norm ⇒ dot)."""
    cand = [c for c in corpus if c["id"] not in exclude_ids]
    sims = np.array([float(np.dot(c["vec"], centroid)) for c in cand])
    return [cand[i] for i in np.argsort(-sims)[:k]]


def intra_sim(recs):
    """Mean pairwise cosine within a rec list (lower = more diverse)."""
    if len(recs) < 2:
        return 0.0
    V = np.array([r["vec"] for r in recs])
    S = V @ V.T
    iu = np.triu_indices(len(recs), k=1)
    return float(S[iu].mean())


def pick_loved(corpus, sub_tastes):
    """Build a persona's 'loved works' = top-N_LOVED corpus works per sub-taste."""
    loved, used = [], set()
    for keys in sub_tastes:
        ranked = sorted(corpus, key=lambda c: -_emo(c["bd"], keys))
        for c in [c for c in ranked if c["id"] not in used][:N_LOVED]:
            used.add(c["id"])
            loved.append(c)
    return loved


async def load_corpus():
    async with async_session() as db:
        items = (await db.scalars(select(MediaItem).where(MediaItem.emotion_vector.isnot(None)))).all()
        return [
            {
                "id": it.id,
                "title": it.title,
                "medium": it.medium,
                "vec": np.array(list(it.emotion_vector), dtype=np.float64),
                "bd": it.emotion_breakdown or {},
            }
            for it in items
        ]


def evaluate(corpus, name, sub_tastes):
    loved = pick_loved(corpus, sub_tastes)
    loved_ids = {c["id"] for c in loved}
    vecs = np.array([c["vec"] for c in loved])
    modes = cluster_taste_modes(vecs, np.ones(len(loved)))
    expected = len(sub_tastes)
    recovered = len(modes) == expected

    print(f"=== {name} ===")
    print(f"  modes found: {len(modes)} / expected {expected}  "
          f"{'✓' if recovered else '✗ MISMATCH'}")

    # Today's behavior: one averaged taste vector. For a split taste this is the
    # 'mushy middle' multi-modal is meant to fix.
    avg = _unit(vecs.mean(axis=0))
    base_recs = retrieve(corpus, avg, loved_ids, LIMIT)
    base_lifts = []
    for keys in sub_tastes:
        ot, bl = _on_target(base_recs, keys), _on_target(corpus, keys)
        base_lifts.append(ot - bl)
        print(f"  single-vector → {keys[0]}…: {ot:.2f} (corpus {bl:.2f}, lift {ot - bl:+.2f})")

    mode_lifts = []
    for i, mode in enumerate(modes):
        members = [loved[j] for j in mode["indices"]]
        emos = mode_label_emotions(members)
        pool = retrieve(corpus, mode["centroid"], loved_ids, POOL)
        keep = mmr_rerank(np.array([r["vec"] for r in pool]), mode["centroid"], k=LIMIT)
        recs = [pool[j] for j in keep]
        ot, bl = _on_target(recs, emos), _on_target(corpus, emos)
        mode_lifts.append(ot - bl)
        media = len({r["medium"] for r in recs})
        print(f"  mode {i + 1} [{' · '.join(emos)}]: on-target {ot:.2f} "
              f"(corpus {bl:.2f}, lift {ot - bl:+.2f}) | media {media}/6 | "
              f"intra-sim {intra_sim(recs):.2f}")
        print(f"          top: {', '.join(r['title'] for r in recs[:4])}")
    print()
    return {
        "recovered": recovered,
        "base_lift": float(np.mean(base_lifts)) if base_lifts else 0.0,
        "mode_lift": float(np.mean(mode_lifts)) if mode_lifts else 0.0,
        "split": expected > 1,
    }


async def main():
    corpus = await load_corpus()
    print(f"\nRecommender eval — {len(corpus)} analyzed works\n"
          f"(on-target = mean rec intensity on the target emotions; lift = vs corpus baseline)\n")
    results = [evaluate(corpus, name, st) for name, st in PERSONAS.items()]

    recovered = sum(r["recovered"] for r in results)
    splits = [r for r in results if r["split"]]
    print("──────── summary ────────")
    print(f"  mode recovery: {recovered}/{len(results)} personas produced the expected mode count")
    if splits:
        mm = float(np.mean([r["mode_lift"] for r in splits]))
        sv = float(np.mean([r["base_lift"] for r in splits]))
        print(f"  split-taste on-target lift — multi-modal {mm:+.2f}  vs  single-vector {sv:+.2f}  "
              f"({mm / sv:.1f}× sharper)" if sv > 0 else
              f"  split-taste on-target lift — multi-modal {mm:+.2f}  vs  single-vector {sv:+.2f}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
