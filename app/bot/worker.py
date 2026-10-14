"""
Railway worker yoki mahalliy polling.

    python -m app.bot.worker

Web servis bilan bir vaqtda webhook ishlatmaslik:
  - Web: TELEGRAM_BOT_MODE=webhook yoki off
  - Worker: TELEGRAM_BOT_MODE=polling
"""

from __future__ import annotations

import asyncio
import logging
import sys

from app.bot.setup import run_polling, shutdown_bot
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("million_istighfor.bot.worker")


async def _main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token.strip():
        raise SystemExit("TELEGRAM_BOT_TOKEN .env da yo‘q")
    if settings.telegram_bot_mode != "polling":
        logger.warning(
            "TELEGRAM_BOT_MODE=%s — polling worker uchun polling qilib o‘rnating",
            settings.telegram_bot_mode,
        )
    logger.info("Webhook o‘chiriladi, long polling boshlanadi…")
    try:
        await run_polling(settings)
    finally:
        await shutdown_bot()


def main() -> None:
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("To‘xtatildi")
        sys.exit(0)


if __name__ == "__main__":
    main()
