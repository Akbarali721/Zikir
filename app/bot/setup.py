from aiogram import Bot, Dispatcher

from app.bot.handlers import router as bot_router
from app.bot.middleware import DbSessionMiddleware
from app.config import Settings

_bot: Bot | None = None
_dispatcher: Dispatcher | None = None


def bot_is_configured(settings: Settings) -> bool:
    return bool(settings.telegram_bot_enabled and settings.telegram_bot_token.strip())


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
    bot, _ = get_bot_and_dispatcher(settings)
    if bot is None:
        return
    base = settings.telegram_webhook_base_url.strip()
    if not base:
        return
    url = f"{base.rstrip('/')}/api/telegram/webhook"
    secret = settings.telegram_webhook_secret.strip()
    if not secret:
        return
    await bot.set_webhook(url=url, secret_token=secret, drop_pending_updates=True)


async def shutdown_bot() -> None:
    global _bot, _dispatcher
    if _bot is not None:
        await _bot.session.close()
    _bot = None
    _dispatcher = None
