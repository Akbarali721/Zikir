from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.daily_contribution import UserDailyContribution
from app.models.user import User
from app.services.daily_service import local_date_for_instant
from app.services.user_identity_service import preferred_display_name as public_display_name


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int
    display_label: str
    dhikr: int
    active_seconds: int


async def get_top10_today(session: AsyncSession) -> list[LeaderboardEntry]:
    settings = get_settings()
    today = local_date_for_instant(datetime.now(timezone.utc), settings.display_timezone)

    stmt = (
        select(UserDailyContribution, User)
        .join(User, User.id == UserDailyContribution.user_id)
        .where(
            UserDailyContribution.local_date == today,
            User.leaderboard_opt_in.is_(True),
            UserDailyContribution.dhikr > 0,
        )
        .order_by(UserDailyContribution.dhikr.desc(), UserDailyContribution.active_seconds.desc())
        .limit(10)
    )
    result = await session.execute(stmt)
    rows = result.all()

    entries: list[LeaderboardEntry] = []
    for idx, (daily, user) in enumerate(rows, start=1):
        entries.append(
            LeaderboardEntry(
                rank=idx,
                display_label=public_display_name(user),
                dhikr=int(daily.dhikr),
                active_seconds=int(daily.active_seconds),
            )
        )
    return entries
