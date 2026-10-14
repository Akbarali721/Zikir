"""Telegram bot (@MillionIstigforBot) — aiogram 3, FastAPI webhook."""

from app.bot.webhook import router as telegram_webhook_router

__all__ = ["telegram_webhook_router"]
