"""Authentication: bcrypt password hashing + JWT carried in an httpOnly cookie.

Because the browser reaches FastAPI through the Next.js /api proxy (same-origin),
the cookie flows without cross-origin/SameSite complications. The token is a signed
JWT (stateless) — no server-side session table.
"""

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

COOKIE_NAME = "access_token"
_ALGO = "HS256"


def hash_password(password: str) -> str:
    # bcrypt operates on <=72 bytes; truncate so long passwords don't error.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.access_token_ttl_days)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.secret_key, algorithm=_ALGO)


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # local http; set True behind https in prod
        max_age=settings.access_token_ttl_days * 86400,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


async def _user_from_token(token: str | None, db: AsyncSession) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGO])
        uid = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    return await db.get(User, uid)


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _user_from_token(access_token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_optional_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    return await _user_from_token(access_token, db)
