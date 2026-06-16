"""3D projection of the emotional space for the /explore visualization.

Reduces the standardized 31-dim emotion vectors to 3D. Uses UMAP when available
(best balance of tight clusters + meaningful global structure), otherwise a pure
numpy PCA fallback so the endpoint always works — UMAP's `numba` dependency can be
awkward to install. Results are cached per method: the corpus is static between
restarts and this is pure arithmetic (no LLM calls), so the first request computes
and the rest are instant.
"""

import logging

import numpy as np
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.media import MediaItem

router = APIRouter(prefix="/api/projection", tags=["projection"])
logger = logging.getLogger(__name__)

# method -> computed result (one global projection of the whole corpus)
_cache: dict[str, dict] = {}


def _pca_3d(X: np.ndarray) -> np.ndarray:
    """Top-3 principal components via SVD. Deterministic, instant, no deps."""
    Xc = X - X.mean(axis=0)
    U, S, _ = np.linalg.svd(Xc, full_matrices=False)
    return U[:, :3] * S[:3]


def _umap_3d(X: np.ndarray) -> np.ndarray:
    import umap  # umap-learn — optional; imported lazily so PCA works without it

    reducer = umap.UMAP(n_components=3, n_neighbors=15, min_dist=0.1, random_state=42)
    return reducer.fit_transform(X)


def _project(method: str, X: np.ndarray) -> tuple[np.ndarray, str]:
    """Return (coords, method_actually_used). Falls back to PCA if UMAP is absent."""
    if method == "umap":
        try:
            return _umap_3d(X), "umap"
        except Exception as e:  # noqa: BLE001 — any import/runtime issue → PCA
            logger.warning("UMAP unavailable (%s); falling back to PCA", e)
    return _pca_3d(X), "pca"


def _axis_labels(coords: np.ndarray, items, top: int = 2) -> list[dict]:
    """Name each rendered axis by the emotions most correlated with it, turning the
    abstract projection axes into readable emotional gradients (neg pole ↔ pos pole)."""
    names = sorted((items[0].emotion_breakdown or {}).keys())
    E = np.array([[(m.emotion_breakdown or {}).get(n, 0.0) for n in names] for m in items])
    axes = []
    for k in range(coords.shape[1]):
        c = coords[:, k] - coords[:, k].mean()
        cn = float(np.sqrt((c ** 2).sum())) or 1.0
        corrs = []
        for j, n in enumerate(names):
            e = E[:, j] - E[:, j].mean()
            en = float(np.sqrt((e ** 2).sum())) or 1.0
            corrs.append((float((c * e).sum() / (cn * en)), n))
        corrs.sort()
        axes.append({
            "neg": [n for _, n in corrs[:top]],
            "pos": [n for _, n in reversed(corrs[-top:])],
        })
    return axes


@router.get("")
async def projection(
    method: str = Query("umap", pattern="^(umap|pca)$"),
    db: AsyncSession = Depends(get_db),
):
    if method in _cache:
        return _cache[method]

    items = (
        await db.execute(select(MediaItem).where(MediaItem.emotion_vector.isnot(None)))
    ).scalars().all()
    if not items:
        return {"method": method, "points": []}

    X = np.array([list(m.emotion_vector) for m in items], dtype=float)
    coords, used = _project(method, X)

    # center on the origin and scale into a tidy unit-ish cube so the view frames
    # nicely no matter which reducer ran.
    coords = coords - coords.mean(axis=0)
    span = float(np.abs(coords).max()) or 1.0
    coords = coords / span

    points = [
        {
            "id": str(m.id),
            "title": m.title,
            "creator": m.creator,
            "medium": m.medium,
            "x": round(float(coords[i, 0]), 4),
            "y": round(float(coords[i, 1]), 4),
            "z": round(float(coords[i, 2]), 4),
            "emotion_breakdown": m.emotion_breakdown,
        }
        for i, m in enumerate(items)
    ]
    result = {"method": used, "axes": _axis_labels(coords, items), "points": points}
    _cache[used] = result
    if used != method:
        _cache[method] = result  # so a repeated umap request also hits cache
    return result
