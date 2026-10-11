from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.daily_contribution import UserDailyContribution


def local_date_for_instant(when: datetime, tz_name: str) -> date:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    return when.astimezone(tz).date()


async def apply_daily_contribution(
    session: AsyncSession,
    user_id: int,
    dhikr_delta: int,
    active_seconds_delta: int,
    *,
    at: datetime | None = None,
) -> None:
    """Sync vaqtidagi kalend kuniga hissa qo‘shadi (client sanasini qabul qilmaydi)."""
    if dhikr_delta == 0 and active_seconds_delta == 0:
        return
    settings = get_settings()
    instant = at or datetime.now(timezone.utc)
    local_day = local_date_for_instant(instant, settings.display_timezone)

    stmt = insert(UserDailyContribution).values(
        user_id=user_id,
        local_date=local_day,
        dhikr=dhikr_delta,
        active_seconds=active_seconds_delta,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "local_date"],
        set_={
            "dhikr": UserDailyContribution.dhikr + stmt.excluded.dhikr,
            "active_seconds": UserDailyContribution.active_seconds + stmt.excluded.active_seconds,
        },
    )
    await session.execute(stmt)


async def get_today_from_daily(session: AsyncSession, user_id: int) -> tuple[int, int]:
    settings = get_settings()
    today = local_date_for_instant(datetime.now(timezone.utc), settings.display_timezone)
    result = await session.execute(
        select(UserDailyContribution.dhikr, UserDailyContribution.active_seconds).where(
            UserDailyContribution.user_id == user_id,
            UserDailyContribution.local_date == today,
        )
    )
    row = result.one_or_none()
    if row is None:
        return 0, 0
    return int(row[0]), int(row[1])
