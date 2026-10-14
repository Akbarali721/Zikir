from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import main_menu_keyboard
from app.config import get_settings
from app.services.bot_stats_service import build_user_stats_message, ensure_bot_user
from app.services.user_identity_service import bind_telegram_chat, sync_profile_from_telegram
from app.services.leaderboard_service import get_top10_today
from app.utils.time_format import format_active_time_uz

router = Router(name="million_istighfor_bot")


async def _answer_html(message_or_callback, text: str) -> None:
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, parse_mode="HTML")
        return
    callback: CallbackQuery = message_or_callback
    if callback.message:
        await callback.message.answer(text, parse_mode="HTML")
    elif callback.from_user and callback.bot:
        await callback.bot.send_message(callback.from_user.id, text, parse_mode="HTML")

WELCOME_TEXT = (
    "🌿 <b>Assalomu alaykum!</b>\n\n"
    "Har kuni telefonimizga vaqt topamiz.\n\n"
    "Instagram, YouTube, xabarlar... "
    "Ba'zan vaqt qanday o'tganini ham sezmay qolamiz.\n\n"
    "Lekin bugun shu vaqtimizning atigi "
    "<b>2 daqiqasini istig‘forga ajratsak-chi?</b> 🤲\n\n"
    "🌙 <b>Million Istig‘for</b> — birgalikda "
    "1 000 000 istig‘for aytish uchun boshlangan "
    "ezgu tashabbus.\n\n"
    "📿 Bugun 33 marta «Astag‘firulloh» "
    "aytishdan boshlang.\n\n"
    "Har bir istig‘foringiz umumiy maqsadimizga "
    "qo‘shiladi. Natijangiz saqlanadi va ertaga "
    "yana davom ettirishingiz mumkin.\n\n"
    "✨ <b>Kichik qadam. Yaxshi odat. "
    "Katta maqsad.</b>\n\n"
    "🤲 Tayyormisiz? Unda boshladik!\n\n"
    "👇 <b>«📿 Zikr qilish» tugmasini bosing.</b>"
)

def _chat_id(message: Message) -> int | None:
    return message.chat.id if message.chat else None


@router.message(CommandStart())
async def on_start(message: Message, db: AsyncSession) -> None:
    if not message.from_user:
        return
    user = await ensure_bot_user(db, message.from_user)
    sync_profile_from_telegram(user, None)
    bind_telegram_chat(user, _chat_id(message))
    await db.flush()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "bot:stats")
async def on_stats(callback: CallbackQuery, db: AsyncSession) -> None:
    if not callback.from_user:
        await callback.answer("Foydalanuvchi aniqlanmadi", show_alert=True)
        return
    user = await ensure_bot_user(db, callback.from_user)
    text = await build_user_stats_message(db, user)
    await _answer_html(callback, text)
    await callback.answer()


@router.callback_query(F.data == "bot:top10")
async def on_top10(callback: CallbackQuery, db: AsyncSession) -> None:
    settings = get_settings()
    entries = await get_top10_today(db)
    if not entries:
        await _answer_html(
            callback,
            "🏆 Bugun hali TOP-10 shakllanmagan.\n"
            "Reytingda ko‘rinish uchun «Reytingda ko‘rinish» tugmasini bosing va zikr qiling.",
        )
        await callback.answer()
        return

    lines = [f"🏆 <b>Bugungi TOP-10</b> ({settings.display_timezone})", ""]
    for row in entries:
        time_label = format_active_time_uz(row.active_seconds)
        lines.append(f"{row.rank}. {row.display_label} — <b>{row.dhikr}</b> ta ({time_label})")
    await _answer_html(callback, "\n".join(lines))
    await callback.answer()


@router.callback_query(F.data == "bot:optin")
async def on_opt_in(callback: CallbackQuery, db: AsyncSession) -> None:
    if not callback.from_user:
        await callback.answer("Xatolik", show_alert=True)
        return
    user = await ensure_bot_user(db, callback.from_user)
    user.leaderboard_opt_in = True
    await db.flush()
    await _answer_html(
        callback,
        "✅ Rozilik qabul qilindi. Bugungi istig‘forlaringiz TOP-10 reytingida ko‘rinishi mumkin.\n"
        "Ismingiz profildagi ko‘rinish nomi yoki Telegram ismingiz bilan chiqadi.",
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
    await _answer_html(callback, "🔒 Endi siz bugungi TOP-10 ro‘yxatida ko‘rinmaysiz.")
    await callback.answer("Reyting o‘chirildi")


@router.callback_query(F.data == "bot:reminder_on")
async def on_reminder_on(callback: CallbackQuery, db: AsyncSession) -> None:
    if not callback.from_user:
        await callback.answer("Xatolik", show_alert=True)
        return
    user = await ensure_bot_user(db, callback.from_user)
    chat_id = callback.message.chat.id if callback.message and callback.message.chat else callback.from_user.id
    bind_telegram_chat(user, chat_id)
    user.reminder_opt_in = True
    await db.flush()
    await _answer_html(
        callback,
        "🔔 Kunlik eslatmalar yoqildi.\n"
        "Ertalab (07:00) va kechqurun (22:00, Toshkent vaqti) xabar olasiz.\n"
        "O‘chirish: «Eslatmalarni o‘chirish».",
    )
    await callback.answer("Eslatmalar yoqildi")


@router.callback_query(F.data == "bot:reminder_off")
async def on_reminder_off(callback: CallbackQuery, db: AsyncSession) -> None:
    if not callback.from_user:
        await callback.answer("Xatolik", show_alert=True)
        return
    user = await ensure_bot_user(db, callback.from_user)
    user.reminder_opt_in = False
    await db.flush()
    await _answer_html(callback, "🔕 Kunlik eslatmalar o‘chirildi.")
    await callback.answer("Eslatmalar o‘chirildi")
