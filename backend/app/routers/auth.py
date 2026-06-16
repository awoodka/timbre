from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    get_optional_user,
    hash_password,
    set_auth_cookie,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas import UserCreate, UserLogin, UserResponse, UserUpdate

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse)
async def signup(data: UserCreate, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.username == data.username))
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name or data.username,
        settings={},
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    set_auth_cookie(response, create_access_token(str(user.id)))
    return user


@router.post("/login", response_model=UserResponse)
async def login(data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == data.username))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    set_auth_cookie(response, create_access_token(str(user.id)))
    return user


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserResponse | None)
async def me(user: User | None = Depends(get_optional_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.settings is not None:
        user.settings = data.settings
    await db.commit()
    await db.refresh(user)
    return user
