from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import GlobalProgress
from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def day_bounds_utc_for_tz(tz_name: str) -> tuple[datetime, datetime]:
    """Start/end of current calendar day in tz_name, as UTC datetimes."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now_local = datetime.now(tz)
    start_local = datetime.combine(now_local.date(), time.min, tzinfo=tz)
    end_local = datetime.combine(now_local.date(), time.max, tzinfo=tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def session_started_on_display_today(session_started_at: datetime, tz_name: str) -> bool:
    if session_started_at.tzinfo is None:
        session_started_at = session_started_at.replace(tzinfo=timezone.utc)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    start_utc, end_utc = day_bounds_utc_for_tz(tz_name)
    return start_utc <= session_started_at.astimezone(timezone.utc) <= end_utc


async def get_today_totals(session: AsyncSession, user_id: int) -> tuple[int, int]:
    from app.services.daily_service import get_today_from_daily

    return await get_today_from_daily(session, user_id)


async def get_current_global_dhikr(session: AsyncSession) -> int:
    result = await session.execute(
        select(GlobalProgress.total_dhikr_count).order_by(GlobalProgress.id).limit(1)
    )
    val = result.scalar_one_or_none()
    return int(val or 0)


def compute_global_growth_since_last_visit(user: User, current_global: int) -> int | None:
    if user.global_dhikr_at_last_visit is None:
        return None
    diff = current_global - user.global_dhikr_at_last_visit
    if diff <= 0:
        return None
    return diff


async def record_visit_snapshot(session: AsyncSession, user: User) -> None:
    current_global = await get_current_global_dhikr(session)
    user.global_dhikr_at_last_visit = current_global
    user.last_visit_at = _utcnow()
