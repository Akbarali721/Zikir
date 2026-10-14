from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.services.reminder_service import process_evening_reminders, process_morning_reminders

logger = logging.getLogger("million_istighfor.bot.scheduler")

_scheduler: AsyncIOScheduler | None = None


def _zikkir_webapp_keyboard():
    from app.bot.keyboards import zikr_webapp_keyboard

    return zikr_webapp_keyboard()


async def start_reminder_scheduler(bot: Bot) -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    tz = ZoneInfo(settings.display_timezone)

    async def send_plain(chat_id: int, text: str, parse_mode: str | None = None):
        await bot.send_message(
            chat_id,
            text,
            parse_mode=parse_mode,
            reply_markup=_zikkir_webapp_keyboard(),
        )

    async def morning_job():
        try:
            n = await process_morning_reminders(
                lambda chat_id, text, parse_mode=None: send_plain(chat_id, text, parse_mode)
            )
            if n:
                logger.info("Ertalab eslatma yuborildi: %s foydalanuvchi", n)
        except Exception:
            logger.exception("Ertalab eslatma xatosi")

    async def evening_job():
        try:
            n = await process_evening_reminders(
                lambda chat_id, text, parse_mode=None: send_plain(chat_id, text, parse_mode)
            )
            if n:
                logger.info("Kechki eslatma yuborildi: %s foydalanuvchi", n)
        except Exception:
            logger.exception("Kechki eslatma xatosi")

    sched = AsyncIOScheduler(timezone=tz)
    sched.add_job(morning_job, trigger="cron", hour=7, minute=0, id="morning_istighfor")
    sched.add_job(evening_job, trigger="cron", hour=22, minute=0, id="evening_stats")
    sched.start()
    _scheduler = sched
    logger.info("Eslatma rejalashtiruvchi ishga tushdi (%s)", settings.display_timezone)
    return sched


async def shutdown_reminder_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
