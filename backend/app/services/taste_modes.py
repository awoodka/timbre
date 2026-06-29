"""Multi-modal taste clustering + MMR diversity for recommendations.

Instead of collapsing a user's whole taste into one averaged vector, group their
*loved* works into a few emotional "modes" (k-means on the standardized, unit-norm
emotion vectors — the same space cosine ranking uses, so Euclidean k-means ≈ cosine
clustering), recommend from each mode's resonance-weighted center, and spread each
row out with MMR. Pure functions (no DB), mirroring services/affinity.py.

Plain numpy + textbook ML (k-means, silhouette, MMR), deterministic (fixed seed) so
a user's modes stay stable between visits.
"""

import numpy as np

MAX_MODES = 3            # never propose more than this many taste modes
MIN_MODE_WORKS = 2       # a mode must be backed by at least this many loved works
SILHOUETTE_MIN = 0.5     # split beyond 1 mode only if clearly separated. Measured: a
                         # single taste blob splits at silhouette ~0.3, genuinely
                         # distinct tastes ~0.9 — so 0.5 separates them and, when in
                         # doubt, under-splits back to one mode (today's behavior).
MMR_LAMBDA = 0.7         # MMR: relevance vs. diversity (1.0 = pure relevance)
_RESTARTS = 8            # k-means restarts (best by inertia); fixed seeds → deterministic


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def _kmeans(X: np.ndarray, k: int, rng: np.random.Generator, iters: int = 50):
    """Lloyd's k-means with k-means++ seeding. Returns (labels, inertia)."""
    n = len(X)
    centers = [X[int(rng.integers(n))]]
    for _ in range(1, k):
        d2 = np.min([np.sum((X - c) ** 2, axis=1) for c in centers], axis=0)
        total = float(d2.sum())
        probs = d2 / total if total > 0 else np.full(n, 1.0 / n)
        centers.append(X[int(rng.choice(n, p=probs))])
    C = np.array(centers, dtype=np.float64)
    labels = np.full(n, -1, dtype=int)
    for it in range(iters):
        new_labels = np.linalg.norm(X[:, None, :] - C[None, :, :], axis=2).argmin(axis=1)
        if it > 0 and np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for j in range(k):
            pts = X[labels == j]
            C[j] = pts.mean(axis=0) if len(pts) else X[int(rng.integers(n))]
    inertia = float(np.sum((X - C[labels]) ** 2))
    return labels, inertia


def _best_kmeans(X: np.ndarray, k: int) -> np.ndarray:
    """Best of several fixed-seed restarts (lowest inertia) → deterministic."""
    best = None
    for r in range(_RESTARTS):
        labels, inertia = _kmeans(X, k, np.random.default_rng(r))
        if best is None or inertia < best[1]:
            best = (labels, inertia)
    return best[0]


def _silhouette(X: np.ndarray, labels: np.ndarray) -> float:
    """Mean silhouette over points: (b - a) / max(a, b), where a = mean intra-cluster
    distance, b = mean distance to the nearest other cluster. -1..1; higher is better."""
    uniq = np.unique(labels)
    if len(uniq) < 2:
        return -1.0
    D = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    s = np.zeros(len(X))
    for i in range(len(X)):
        same = labels == labels[i]
        same[i] = False
        a = D[i, same].mean() if same.any() else 0.0
        b = min(
            D[i, labels == c].mean()
            for c in uniq
            if c != labels[i] and (labels == c).any()
        )
        s[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0.0
    return float(s.mean())


def _mode_from(X: np.ndarray, w: np.ndarray, idx: np.ndarray) -> dict:
    """Build a mode from member indices: resonance-weighted unit centroid + weight."""
    members, ww = X[idx], w[idx]
    wsum = float(ww.sum())
    center = (members * ww[:, None]).sum(axis=0) / wsum if wsum > 0 else members.mean(axis=0)
    return {"indices": [int(i) for i in idx], "centroid": _unit(center), "weight": wsum}


def cluster_taste_modes(
    vectors, weights, *, max_k=MAX_MODES, min_mode_works=MIN_MODE_WORKS, sil_min=SILHOUETTE_MIN
) -> list[dict]:
    """Group a user's loved works into 1..max_k taste modes.

    vectors: (n, d) standardized unit-norm emotion vectors of the loved works.
    weights: (n,) per-work weight (resonance) — pulls each mode's center.

    Returns modes sorted by weight (strongest taste first), each a dict:
      {"indices": [int...], "centroid": unit vec (d,), "weight": float}.
    Falls back to a single mode when there aren't enough works or no split is clean
    enough (silhouette < sil_min), so a single-modal taste behaves exactly as today.
    """
    X = np.asarray(vectors, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    n = len(X)
    one_mode = lambda: [_mode_from(X, w, np.arange(n))]
    if n < min_mode_works * 2:
        return one_mode()

    best_labels, best_k, best_sil = None, 1, -1.0
    for k in range(2, min(max_k, n // min_mode_works) + 1):
        labels = _best_kmeans(X, k)
        if (np.bincount(labels, minlength=k) < min_mode_works).any():
            continue  # a cluster too small to be a real "mode"
        sil = _silhouette(X, labels)
        if sil > best_sil:
            best_labels, best_k, best_sil = labels, k, sil

    if best_labels is None or best_sil < sil_min:
        return one_mode()
    modes = [_mode_from(X, w, np.where(best_labels == j)[0]) for j in range(best_k)]
    modes.sort(key=lambda m: -m["weight"])
    return modes


def mmr_rerank(cand_vecs, query_vec, *, k, lam=MMR_LAMBDA) -> list[int]:
    """Greedy Maximal Marginal Relevance over candidate rows.

    Each step picks the candidate maximizing
        lam * cos(c, query) - (1 - lam) * max_{s in chosen} cos(c, s).
    lam=1 → pure relevance (cosine) order; lower lam pushes picks apart for variety.
    Inputs are unit-norm, so dot products are cosines. Returns selected row indices.
    """
    V = np.asarray(cand_vecs, dtype=np.float64)
    if len(V) == 0:
        return []
    q = np.asarray(query_vec, dtype=np.float64)
    rel = V @ q
    sim = V @ V.T
    chosen, remaining = [], list(range(len(V)))
    while remaining and len(chosen) < k:
        if not chosen:
            pick = remaining[int(np.argmax(rel[remaining]))]
        else:
            scores = [(lam * rel[i] - (1 - lam) * max(sim[i, j] for j in chosen), i) for i in remaining]
            pick = max(scores)[1]
        chosen.append(pick)
        remaining.remove(pick)
    return chosen
