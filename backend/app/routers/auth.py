from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
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
from app.models.user import Rating, User
from app.schemas import (
    AccountDelete,
    PasswordChange,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.feedback import build_taste_profile

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
    if data.username is not None and data.username != user.username:
        clash = await db.scalar(select(User).where(User.username == data.username))
        if clash:
            raise HTTPException(status_code=409, detail="Username already taken")
        user.username = data.username
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.settings is not None:
        # Shallow-merge so independent prefs (theme, lean_enjoyment) don't clobber.
        user.settings = {**user.settings, **data.settings}
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Username already taken")
    await db.refresh(user)
    return user


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"ok": True}


@router.post("/reset-ratings")
async def reset_ratings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await db.execute(delete(Rating).where(Rating.user_id == user.id))
    await db.commit()
    return {"ok": True}


@router.get("/export")
async def export_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ratings = list(await db.scalars(select(Rating).where(Rating.user_id == user.id)))
    taste = build_taste_profile([r.feedback for r in ratings]) if ratings else None
    return {
        "account": {
            "username": user.username,
            "display_name": user.display_name,
            "created_at": user.created_at.isoformat(),
        },
        "ratings": [
            {
                "media_id": str(r.media_id),
                "feedback": r.feedback,
                "resonance": r.resonance,
                "enjoyment": r.enjoyment,
            }
            for r in ratings
        ],
        "taste_profile": taste.tolist() if taste is not None else None,
    }


@router.post("/delete-account")
async def delete_account(
    data: AccountDelete,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Password is incorrect")
    await db.delete(user)  # FK ondelete=CASCADE removes ratings + saved_items
    await db.commit()
    clear_auth_cookie(response)
    return {"ok": True}
