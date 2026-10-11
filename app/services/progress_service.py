from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import GlobalProgress
from app.schemas.progress import GlobalProgressStats, PersonalProgress, ProgressResponse


async def ensure_global_progress(session: AsyncSession) -> GlobalProgress:
    result = await session.execute(select(GlobalProgress).order_by(GlobalProgress.id).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        row = GlobalProgress()
        session.add(row)
        await session.flush()
    return row


def _percent(part: int, goal: int) -> float:
    if goal <= 0:
        return 0.0
    return round(min(part, goal) / goal * 100, 3)


def build_progress_response(user_dhikr: int, user_seconds: int, global_row: GlobalProgress) -> ProgressResponse:
    remaining_dhikr = max(0, global_row.dhikr_goal - global_row.total_dhikr_count)
    remaining_seconds = max(0, global_row.seconds_goal - global_row.total_active_seconds)

    return ProgressResponse(
        personal=PersonalProgress(dhikr=user_dhikr, active_seconds=user_seconds),
        global_=GlobalProgressStats(
            dhikr=global_row.total_dhikr_count,
            dhikr_goal=global_row.dhikr_goal,
            dhikr_percent=_percent(global_row.total_dhikr_count, global_row.dhikr_goal),
            remaining_dhikr=remaining_dhikr,
            active_seconds=global_row.total_active_seconds,
            seconds_goal=global_row.seconds_goal,
            time_percent=_percent(global_row.total_active_seconds, global_row.seconds_goal),
            remaining_seconds=remaining_seconds,
        ),
    )
