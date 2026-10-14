from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import get_settings


def webapp_url() -> str:
    settings = get_settings()
    base = (settings.telegram_webapp_url or settings.telegram_webhook_base_url or "").strip()
    if not base:
        return "https://example.com/"
    return base if base.endswith("/") else f"{base}/"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📿 Zikr qilish",
                    web_app=WebAppInfo(url=webapp_url()),
                )
            ],
            [
                InlineKeyboardButton(text="📊 Statistikam", callback_data="bot:stats"),
                InlineKeyboardButton(text="🏆 TOP-10", callback_data="bot:top10"),
            ],
            [
                InlineKeyboardButton(text="📋 Reytingda ko‘rinish", callback_data="bot:optin"),
                InlineKeyboardButton(text="🔒 Reytingdan chiqish", callback_data="bot:optout"),
            ],
        ]
    )
