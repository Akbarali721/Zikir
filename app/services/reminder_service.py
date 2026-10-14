from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.services.daily_service import get_today_from_daily, local_date_for_instant
from app.services.user_identity_service import preferred_display_name


def tashkent_today() -> datetime:
    return datetime.now(timezone.utc)


async def users_due_for_reminders(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(
            User.reminder_opt_in.is_(True),
            User.telegram_chat_id.isnot(None),
        )
    )
    return list(result.scalars().all())


async def process_morning_reminders(send_message) -> int:
    """07:00 — 33 ta istig‘for taklifi. Bir kun bir marta."""
    settings = get_settings()
    today = local_date_for_instant(tashkent_today(), settings.display_timezone)
    sent = 0
    async with AsyncSessionLocal() as session:
        for user in await users_due_for_reminders(session):
            if user.reminder_last_morning_date == today:
                continue
            name = preferred_display_name(user)
            text = (
                f"Xayrli tong, {name}! ☀️\n\n"
                "Yangi kunning barakasini 33 ta istig‘for bilan boshlang.\n"
                "📿 Zikr qilish tugmasi orqali WebApp ga o‘ting."
            )
            await send_message(user.telegram_chat_id, text)
            user.reminder_last_morning_date = today
            sent += 1
        await session.commit()
    return sent


async def process_evening_reminders(send_message) -> int:
    """22:00 — bugungi haqiqiy statistika."""
    settings = get_settings()
    today = local_date_for_instant(tashkent_today(), settings.display_timezone)
    sent = 0
    async with AsyncSessionLocal() as session:
        for user in await users_due_for_reminders(session):
            if user.reminder_last_evening_date == today:
                continue
            today_dhikr, today_seconds = await get_today_from_daily(session, user.id)
            name = preferred_display_name(user)
            from app.utils.time_format import format_active_time_uz

            text = (
                f"Xayrli kech, {name}! 🌙\n\n"
                f"Bugun siz <b>{today_dhikr}</b> ta istig‘for aytdingiz.\n"
                f"Faol vaqt: {format_active_time_uz(today_seconds)}.\n\n"
                "Ertaga yana birga davom etamiz — 📿 Zikr qilish tugmasi bilan."
            )
            await send_message(user.telegram_chat_id, text, parse_mode="HTML")
            user.reminder_last_evening_date = today
            sent += 1
        await session.commit()
    return sent
