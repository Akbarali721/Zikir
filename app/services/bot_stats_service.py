from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.daily_service import get_today_from_daily
from app.services.telegram import get_or_create_user
from app.utils.time_format import format_active_time_uz


def tg_user_from_aiogram(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


async def ensure_bot_user(session: AsyncSession, tg_user) -> User:
    return await get_or_create_user(session, tg_user_from_aiogram(tg_user))


async def build_user_stats_message(session: AsyncSession, user: User) -> str:
    today_dhikr, today_seconds = await get_today_from_daily(session, user.id)
    total_dhikr = int(user.personal_dhikr_count)
    total_seconds = int(user.personal_active_seconds)

    lines = [
        "📊 <b>Statistikangiz</b> (1 million istig‘for)",
        "",
        f"Bugun: <b>{today_dhikr}</b> ta istig‘for",
        f"Bugungi faol vaqt: {format_active_time_uz(today_seconds)}",
        "",
        f"Jami: <b>{total_dhikr}</b> ta istig‘for",
        f"Jami faol vaqt: {format_active_time_uz(total_seconds)}",
    ]
    if user.leaderboard_opt_in:
        lines.append("")
        lines.append("🏆 Siz bugungi TOP-10 reytingda ko‘rinishga rozilik bergansiz.")
    else:
        lines.append("")
        lines.append(
            "ℹ️ TOP-10 ro‘yxatida chiqish uchun «Reytingda ko‘rinish» tugmasini bosing."
        )
    return "\n".join(lines)
