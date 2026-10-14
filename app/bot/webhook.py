from typing import Annotated

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from app.bot.setup import bot_is_configured, get_bot_and_dispatcher
from app.config import get_settings

router = APIRouter(prefix="/api/telegram", tags=["telegram-bot"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Telegram Bot API webhook (aiogram 3). Faqat FastAPI ichida ishlaydi."""
    settings = get_settings()
    if not bot_is_configured(settings):
        raise HTTPException(status_code=503, detail="Telegram bot disabled or not configured")

    expected = settings.telegram_webhook_secret.strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="TELEGRAM_WEBHOOK_SECRET is not configured",
        )
    if x_telegram_bot_api_secret_token != expected:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    bot, dispatcher = get_bot_and_dispatcher(settings)
    if bot is None or dispatcher is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    try:
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": bot})
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Telegram update") from exc

    await dispatcher.feed_update(bot, update)
    return {"ok": "true"}
