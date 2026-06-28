import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
import app.models.user  # noqa: F401  -- register User/Rating tables with Base.metadata
import app.models.rec_explanation  # noqa: F401  -- register RecExplanation table
from app.routers import media, recommend, dimensions, auth, ratings, saves, projection

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="MediaFingerprint",
    description="Cross-media emotional recommendation engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(media.router)
app.include_router(recommend.router)
app.include_router(dimensions.router)
app.include_router(auth.router)
app.include_router(ratings.router)
app.include_router(saves.router)
app.include_router(projection.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
