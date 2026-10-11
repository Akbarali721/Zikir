from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.daily_contribution import UserDailyContribution
from app.models.progress import GlobalProgress
from app.models.tasbeh_session import TasbehSession
from app.models.user import User
from app.models.visit import UserVisit
from app.services.daily_service import local_date_for_instant


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _today_local() -> date:
    settings = get_settings()
    return local_date_for_instant(_utcnow(), settings.display_timezone)


def _day_bounds_utc(local_day: date, tz_name: str) -> tuple[datetime, datetime]:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    start = datetime.combine(local_day, datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
    end = datetime.combine(local_day, datetime.max.time(), tzinfo=tz).astimezone(timezone.utc)
    return start, end


async def get_overview(session: AsyncSession) -> dict:
    settings = get_settings()
    now = _utcnow()
    online_cutoff = now - timedelta(seconds=settings.online_window_seconds)
    dhikr_cutoff = now - timedelta(seconds=settings.dhikring_window_seconds)
    today = _today_local()
    start_utc, end_utc = _day_bounds_utc(today, settings.display_timezone)

    total_users = int(await session.scalar(select(func.count()).select_from(User)) or 0)

    today_visits = int(
        await session.scalar(
            select(func.count())
            .select_from(UserVisit)
            .where(UserVisit.started_at >= start_utc, UserVisit.started_at <= end_utc)
        )
        or 0
    )

    today_distinct_visitors = int(
        await session.scalar(
            select(func.count(func.distinct(UserVisit.user_id))).where(
                UserVisit.started_at >= start_utc, UserVisit.started_at <= end_utc
            )
        )
        or 0
    )

    today_new_users = int(
        await session.scalar(
            select(func.count()).select_from(User).where(User.created_at >= start_utc, User.created_at <= end_utc)
        )
        or 0
    )

    online_users = int(
        await session.scalar(
            select(func.count(func.distinct(UserVisit.user_id))).where(
                UserVisit.ended_at.is_(None),
                UserVisit.last_seen_at >= online_cutoff,
            )
        )
        or 0
    )

    dhikring_users = int(
        await session.scalar(
            select(func.count()).select_from(User).where(User.last_dhikr_at.isnot(None), User.last_dhikr_at >= dhikr_cutoff)
        )
        or 0
    )

    global_row = await session.scalar(select(GlobalProgress).order_by(GlobalProgress.id).limit(1))
    total_dhikr = int(global_row.total_dhikr_count if global_row else 0)
    total_seconds = int(global_row.total_active_seconds if global_row else 0)

    td_result = await session.execute(
        select(
            func.coalesce(func.sum(UserDailyContribution.dhikr), 0),
            func.coalesce(func.sum(UserDailyContribution.active_seconds), 0),
        ).where(UserDailyContribution.local_date == today)
    )
    td_row = td_result.one()

    return {
        "generated_at": now,
        "total_users": total_users,
        "today_distinct_visitors": today_distinct_visitors,
        "today_new_users": today_new_users,
        "today_visits": today_visits,
        "online_users": online_users,
        "dhikring_users": dhikring_users,
        "total_dhikr": total_dhikr,
        "today_dhikr": int(td_row[0]),
        "total_active_seconds": total_seconds,
        "today_active_seconds": int(td_row[1]),
        "display_timezone": settings.display_timezone,
    }


async def list_users(
    session: AsyncSession,
    *,
    q: str | None,
    page: int,
    page_size: int,
    onboarding: str | None,
    online_only: bool,
) -> dict:
    settings = get_settings()
    online_cutoff = _utcnow() - timedelta(seconds=settings.online_window_seconds)
    page_size = min(max(page_size, 1), 100)
    offset = (max(page, 1) - 1) * page_size

    stmt = select(User)
    if q:
        q = q.strip()
        filters = []
        if q.isdigit():
            filters.append(User.telegram_id == int(q))
        filters.append(User.display_name.ilike(f"%{q}%"))
        filters.append(User.username.ilike(f"%{q}%"))
        filters.append(User.first_name.ilike(f"%{q}%"))
        stmt = stmt.where(or_(*filters))
    if onboarding == "completed":
        stmt = stmt.where(User.onboarding_completed.is_(True))
    elif onboarding == "pending":
        stmt = stmt.where(User.onboarding_completed.is_(False))

    if online_only:
        subq = (
            select(UserVisit.user_id)
            .where(UserVisit.ended_at.is_(None), UserVisit.last_seen_at >= online_cutoff)
            .distinct()
        )
        stmt = stmt.where(User.id.in_(subq))

    count_stmt = select(func.count()).select_from(User)
    if q:
        q = q.strip()
        filters = []
        if q.isdigit():
            filters.append(User.telegram_id == int(q))
        filters.append(User.display_name.ilike(f"%{q}%"))
        filters.append(User.username.ilike(f"%{q}%"))
        filters.append(User.first_name.ilike(f"%{q}%"))
        count_stmt = count_stmt.where(or_(*filters))
    if onboarding == "completed":
        count_stmt = count_stmt.where(User.onboarding_completed.is_(True))
    elif onboarding == "pending":
        count_stmt = count_stmt.where(User.onboarding_completed.is_(False))
    if online_only:
        subq = (
            select(UserVisit.user_id)
            .where(UserVisit.ended_at.is_(None), UserVisit.last_seen_at >= online_cutoff)
            .distinct()
        )
        count_stmt = count_stmt.where(User.id.in_(subq))

    total = int(await session.scalar(count_stmt) or 0)
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    users = (await session.execute(stmt)).scalars().all()

    items = []
    for u in users:
        visit_count = int(
            await session.scalar(select(func.count()).select_from(UserVisit).where(UserVisit.user_id == u.id)) or 0
        )
        last_seen = await session.scalar(
            select(func.max(UserVisit.last_seen_at)).where(UserVisit.user_id == u.id)
        )
        items.append(
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "display_name": u.display_name,
                "first_name": u.first_name,
                "onboarding_completed": u.onboarding_completed,
                "created_at": u.created_at,
                "last_seen_at": last_seen,
                "last_dhikr_at": u.last_dhikr_at,
                "visit_count": visit_count,
                "personal_dhikr_count": u.personal_dhikr_count,
                "personal_active_seconds": u.personal_active_seconds,
            }
        )

    return {"total": total, "page": page, "page_size": page_size, "items": items}


async def get_user_detail(session: AsyncSession, user_id: int) -> dict | None:
    user = await session.get(User, user_id)
    if user is None:
        return None
    visits = (
        await session.execute(
            select(UserVisit).where(UserVisit.user_id == user_id).order_by(UserVisit.started_at.desc()).limit(20)
        )
    ).scalars().all()
    sessions = (
        await session.execute(
            select(TasbehSession).where(TasbehSession.user_id == user_id).order_by(TasbehSession.started_at.desc()).limit(20)
        )
    ).scalars().all()
    daily = (
        await session.execute(
            select(UserDailyContribution)
            .where(UserDailyContribution.user_id == user_id)
            .order_by(UserDailyContribution.local_date.desc())
            .limit(30)
        )
    ).scalars().all()
    return {
        "user": user,
        "visits": visits,
        "sessions": sessions,
        "daily": daily,
    }


async def daily_series(session: AsyncSession, days: int) -> list[dict]:
    settings = get_settings()
    today = _today_local()
    start_day = today - timedelta(days=max(days - 1, 0))
    result = await session.execute(
        select(
            UserDailyContribution.local_date,
            func.coalesce(func.sum(UserDailyContribution.dhikr), 0),
            func.coalesce(func.sum(UserDailyContribution.active_seconds), 0),
            func.count(func.distinct(UserDailyContribution.user_id)),
        )
        .where(UserDailyContribution.local_date >= start_day, UserDailyContribution.local_date <= today)
        .group_by(UserDailyContribution.local_date)
        .order_by(UserDailyContribution.local_date)
    )
    by_day = {row[0]: row for row in result.all()}
    series = []
    for i in range(days):
        d = start_day + timedelta(days=i)
        row = by_day.get(d)
        visitors = int(
            await session.scalar(
                select(func.count(func.distinct(UserVisit.user_id))).where(
                    UserVisit.started_at >= _day_bounds_utc(d, settings.display_timezone)[0],
                    UserVisit.started_at <= _day_bounds_utc(d, settings.display_timezone)[1],
                )
            )
            or 0
        )
        series.append(
            {
                "date": d.isoformat(),
                "visitors": visitors,
                "dhikr": int(row[1]) if row else 0,
                "active_seconds": int(row[2]) if row else 0,
                "contributors": int(row[3]) if row else 0,
            }
        )
    return series


async def funnel_stats(session: AsyncSession, days: int) -> dict:
    settings = get_settings()
    today = _today_local()
    start_day = today - timedelta(days=max(days - 1, 0))
    start_utc, _ = _day_bounds_utc(start_day, settings.display_timezone)
    _, end_utc = _day_bounds_utc(today, settings.display_timezone)

    visits = int(
        await session.scalar(
            select(func.count())
            .select_from(UserVisit)
            .where(UserVisit.started_at >= start_utc, UserVisit.started_at <= end_utc, UserVisit.ended_at.isnot(None))
        )
        or 0
    )
    started_dhikr = int(
        await session.scalar(
            select(func.count())
            .select_from(UserVisit)
            .where(
                UserVisit.started_at >= start_utc,
                UserVisit.started_at <= end_utc,
                UserVisit.ended_at.isnot(None),
                UserVisit.first_dhikr_at.isnot(None),
            )
        )
        or 0
    )
    left_without = max(0, visits - started_dhikr)
    new_users = int(
        await session.scalar(
            select(func.count()).select_from(User).where(User.created_at >= start_utc, User.created_at <= end_utc)
        )
        or 0
    )
    onboarded = int(
        await session.scalar(
            select(func.count()).select_from(User).where(
                User.created_at >= start_utc, User.created_at <= end_utc, User.onboarding_completed.is_(True)
            )
        )
        or 0
    )
    return {
        "period_days": days,
        "completed_visits": visits,
        "visits_with_dhikr": started_dhikr,
        "left_without_dhikr": left_without,
        "new_users": new_users,
        "onboarded_new_users": onboarded,
    }
