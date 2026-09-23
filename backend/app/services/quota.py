"""Daily allowances for the actions that cost Gemini money, and a per-IP cap on sign-ups.

Sign-ups are open, so every account gets a small daily allowance of new works (each one
is two Gemini calls plus scraping), explanations and free-text searches. A site-wide
ceiling on top of that bounds the bill no matter how many accounts someone makes, and
the per-IP sign-up cap keeps account farming slow.

Counts live in the `usage_counters` table (one row per UTC day, subject and action), so
they're shared across workers and survive restarts. A request is counted before the work
happens; one that goes over a limit still counts, which only matters for that day.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# action -> (settings attribute with the per-user limit, how to name it in the error)
_PER_USER = {
    "add": ("daily_new_works_per_user", "new works"),
    "explain": ("daily_explanations_per_user", "explanations"),
    "search": ("daily_searches_per_user", "described-feeling searches"),
}


def client_ip(request: Request) -> str:
    """Best-effort client IP — prefers Cloudflare / proxy headers, falls back to peer."""
    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _bump(db: AsyncSession, subject: str, action: str) -> int:
    """Add one to today's counter for (subject, action) and return the new count."""
    count = await db.scalar(
        text(
            """
            INSERT INTO usage_counters (day, subject, action, count)
            VALUES (:day, :subject, :action, 1)
            ON CONFLICT (day, subject, action)
            DO UPDATE SET count = usage_counters.count + 1
            RETURNING count
            """
        ),
        {
            "day": datetime.now(timezone.utc).date(),
            "subject": subject,
            "action": action,
        },
    )
    await db.commit()
    return count


async def charge_ai(db: AsyncSession, action: str, user=None) -> None:
    """Count one Gemini-backed `action` ("add", "explain" or "search") for `user` (None for
    an anonymous visitor, whose own cap lives in the recommend router) and against the
    site-wide total. Raises 429 once either limit is passed for the day."""
    if user is not None:
        attr, label = _PER_USER[action]
        limit = getattr(settings, attr)
        if await _bump(db, f"user:{user.id}", action) > limit:
            raise HTTPException(
                status_code=429,
                detail=f"You've used today's {limit} {label}. The limit resets at midnight UTC.",
            )
    if await _bump(db, "all", "ai") > settings.daily_ai_actions_total:
        raise HTTPException(
            status_code=429,
            detail="Timbre has hit its daily limit for AI features. Please try again tomorrow.",
        )


async def charge_signup(db: AsyncSession, request: Request) -> None:
    """Count one sign-up from this request's IP; raises 429 past the daily cap."""
    if await _bump(db, f"ip:{client_ip(request)}", "signup") > settings.signups_per_ip_per_day:
        raise HTTPException(
            status_code=429,
            detail="Too many new accounts from this network today. Please try again tomorrow.",
        )
