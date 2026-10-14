from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import main_menu_keyboard
from app.config import get_settings
from app.services.bot_stats_service import build_user_stats_message, ensure_bot_user
from app.services.leaderboard_service import get_top10_today
from app.utils.time_format import format_active_time_uz

router = Router(name="million_istighfor_bot")

WELCOME_TEXT = (
    "Assalomu alaykum! 👋\n\n"
    "<b>Million Istig‘for</b> — jamoaviy zikr va bir million istig‘for maqsadiga qo‘shiling.\n\n"
    "📿 <b>Zikr qilish</b> — WebApp orqali zikr sanash.\n"
    "📊 <b>Statistikam</b> — bugungi va jami istig‘foringiz.\n"
    "🏆 <b>TOP-10</b> — bugungi eng faol 10 ishtirokchi "
    "(faqat reytingda ko‘rinishga rozilik berganlar).\n\n"
    "Quyidagi tugmalardan birini tanlang:"
)


@router.message(CommandStart())
async def on_start(message: Message, db: AsyncSession) -> None:
    if not message.from_user:
        return
    await ensure_bot_user(db, message.from_user)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "bot:stats")
async def on_stats(callback: CallbackQuery, db: AsyncSession) -> None:
    if not callback.from_user:
        await callback.answer("Foydalanuvchi aniqlanmadi", show_alert=True)
        return
    user = await ensure_bot_user(db, callback.from_user)
    text = await build_user_stats_message(db, user)
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "bot:top10")
async def on_top10(callback: CallbackQuery, db: AsyncSession) -> None:
    settings = get_settings()
    entries = await get_top10_today(db)
    if not entries:
        await callback.message.answer(
            "🏆 Bugun hali TOP-10 shakllanmagan.\n"
            "Reytingda ko‘rinish uchun «Reytingda ko‘rinish» tugmasini bosing va zikr qiling.",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    lines = [f"🏆 <b>Bugungi TOP-10</b> ({settings.display_timezone})", ""]
    for row in entries:
        time_label = format_active_time_uz(row.active_seconds)
        lines.append(f"{row.rank}. {row.display_label} — <b>{row.dhikr}</b> ta ({time_label})")
    await callback.message.answer("\n".join(lines), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "bot:optin")
async def on_opt_in(callback: CallbackQuery, db: AsyncSession) -> None:
    if not callback.from_user:
        await callback.answer("Xatolik", show_alert=True)
        return
    user = await ensure_bot_user(db, callback.from_user)
    user.leaderboard_opt_in = True
    await db.flush()
    await callback.message.answer(
        "✅ Rozilik qabul qilindi. Bugungi istig‘forlaringiz TOP-10 reytingida ko‘rinishi mumkin.\n"
        "Ismingiz profildagi ko‘rinish nomi yoki Telegram ismingiz bilan chiqadi.",
        parse_mode="HTML",
    )
    await callback.answer("Reyting yoqildi")


@router.callback_query(F.data == "bot:optout")
async def on_opt_out(callback: CallbackQuery, db: AsyncSession) -> None:
    if not callback.from_user:
        await callback.answer("Xatolik", show_alert=True)
        return
    user = await ensure_bot_user(db, callback.from_user)
    user.leaderboard_opt_in = False
    await db.flush()
    await callback.message.answer(
        "🔒 Endi siz bugungi TOP-10 ro‘yxatida ko‘rinmaysiz.",
        parse_mode="HTML",
    )
    await callback.answer("Reyting o‘chirildi")
