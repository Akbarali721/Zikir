import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.models.visit import UserVisit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _visit_idle_timeout() -> timedelta:
    settings = get_settings()
    return timedelta(minutes=settings.visit_idle_timeout_minutes)


async def get_visit_for_user(
    session: AsyncSession, user_id: int, visit_id: uuid.UUID | None
) -> UserVisit | None:
    if visit_id is None:
        return None
    result = await session.execute(
        select(UserVisit).where(UserVisit.id == visit_id, UserVisit.user_id == user_id)
    )
    visit = result.scalar_one_or_none()
    if visit is None or visit.ended_at is not None:
        return None
    if _utcnow() - visit.last_seen_at > _visit_idle_timeout():
        visit.ended_at = visit.last_seen_at
        await session.flush()
        return None
    return visit


async def ensure_active_visit(
    session: AsyncSession,
    user: User,
    *,
    visit_id: uuid.UUID | None,
    route: str | None,
) -> UserVisit:
    now = _utcnow()
    visit = await get_visit_for_user(session, user.id, visit_id)
    if visit is not None:
        visit.last_seen_at = now
        if route:
            visit.last_route = route[:64]
        await session.flush()
        return visit

    visit = UserVisit(user_id=user.id, started_at=now, last_seen_at=now, last_route=route[:64] if route else None)
    session.add(visit)
    await session.flush()
    return visit


async def heartbeat(
    session: AsyncSession,
    user: User,
    *,
    visit_id: uuid.UUID | None,
    route: str | None,
) -> UserVisit:
    return await ensure_active_visit(session, user, visit_id=visit_id, route=route)


async def mark_first_dhikr(session: AsyncSession, user: User, visit: UserVisit | None) -> None:
    now = _utcnow()
    user.last_dhikr_at = now
    if visit and visit.first_dhikr_at is None:
        visit.first_dhikr_at = now
    if visit:
        visit.last_dhikr_at = now
        visit.last_seen_at = now


async def end_stale_visits(session: AsyncSession) -> None:
    """Background emas — admin statistikada eski tashriflarni yopish uchun ixtiyoriy."""
    cutoff = _utcnow() - _visit_idle_timeout()
    await session.execute(
        update(UserVisit)
        .where(UserVisit.ended_at.is_(None), UserVisit.last_seen_at < cutoff)
        .values(ended_at=UserVisit.last_seen_at)
    )
