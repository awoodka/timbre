from fastapi import APIRouter

from app.dimensions import EMOTIONAL_DIMENSIONS
from app.schemas import DimensionResponse

router = APIRouter(prefix="/api", tags=["dimensions"])


@router.get("/dimensions", response_model=list[DimensionResponse])
async def get_dimensions():
    return [
        DimensionResponse(key=d["key"], name=d["name"], description=d["description"])
        for d in EMOTIONAL_DIMENSIONS
    ]
