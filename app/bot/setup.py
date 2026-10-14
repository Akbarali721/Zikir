from aiogram import Bot, Dispatcher

from app.bot.handlers import router as bot_router
from app.bot.middleware import DbSessionMiddleware
from app.config import Settings

_bot: Bot | None = None
_dispatcher: Dispatcher | None = None


def bot_is_configured(settings: Settings) -> bool:
    return bool(
        settings.telegram_bot_enabled
        and settings.telegram_bot_mode != "off"
        and settings.telegram_bot_token.strip()
    )


def should_register_webhook(settings: Settings) -> bool:
    return bool(
        bot_is_configured(settings)
        and settings.telegram_bot_mode == "webhook"
        and settings.telegram_webhook_base_url.strip()
        and settings.telegram_webhook_secret.strip()
    )


def get_bot_and_dispatcher(settings: Settings) -> tuple[Bot | None, Dispatcher | None]:
    global _bot, _dispatcher
    if not bot_is_configured(settings):
        return None, None
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token.strip())
        _dispatcher = Dispatcher()
        _dispatcher.update.middleware(DbSessionMiddleware())
        _dispatcher.include_router(bot_router)
    return _bot, _dispatcher


async def configure_webhook(settings: Settings) -> None:
    if not should_register_webhook(settings):
        return
    bot, _ = get_bot_and_dispatcher(settings)
    if bot is None:
        return
    base = settings.telegram_webhook_base_url.strip()
    url = f"{base.rstrip('/')}/api/telegram/webhook"
    secret = settings.telegram_webhook_secret.strip()
    await bot.set_webhook(url=url, secret_token=secret, drop_pending_updates=True)


async def clear_webhook_for_polling(settings: Settings) -> None:
    """Polling boshlashdan oldin — Telegram yangilanishlari webhook emas, long polling ga o‘tadi."""
    bot, _ = get_bot_and_dispatcher(settings)
    if bot is None:
        raise RuntimeError("TELEGRAM_BOT_TOKEN sozlanmagan yoki bot o‘chirilgan")
    await bot.delete_webhook(drop_pending_updates=True)


async def run_polling(settings: Settings) -> None:
    if settings.telegram_bot_mode != "polling":
        raise RuntimeError("TELEGRAM_BOT_MODE=polling bo‘lishi kerak")
    bot, dispatcher = get_bot_and_dispatcher(settings)
    if bot is None or dispatcher is None:
        raise RuntimeError("Bot sozlanmagan")
    await clear_webhook_for_polling(settings)
    from app.bot.scheduler import start_reminder_scheduler

    await start_reminder_scheduler(bot)
    try:
        await dispatcher.start_polling(bot)
    finally:
        from app.bot.scheduler import shutdown_reminder_scheduler

        await shutdown_reminder_scheduler()


async def shutdown_bot() -> None:
    global _bot, _dispatcher
    if _bot is not None:
        await _bot.session.close()
    _bot = None
    _dispatcher = None
