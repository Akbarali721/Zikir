import pytest

from app.bot.setup import should_register_webhook
from app.config import Settings


def test_webhook_skipped_in_polling_mode(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1:abc")
    monkeypatch.setenv("TELEGRAM_BOT_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_MODE", "polling")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_BASE_URL", "https://zikir-production.up.railway.app")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    s = Settings()
    assert s.telegram_bot_mode == "polling"
    assert should_register_webhook(s) is False


def test_webhook_enabled_when_configured(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1:abc")
    monkeypatch.setenv("TELEGRAM_BOT_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_MODE", "webhook")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_BASE_URL", "https://zikir-production.up.railway.app")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    s = Settings()
    assert should_register_webhook(s) is True


@pytest.mark.asyncio
async def test_clear_webhook_for_polling(monkeypatch):
    deleted = {"called": False}

    class FakeBot:
        async def delete_webhook(self, drop_pending_updates=False):
            deleted["called"] = True

    from app.bot import setup as bot_setup

    bot_setup._bot = FakeBot()
    bot_setup._dispatcher = None

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1:abc")
    monkeypatch.setenv("TELEGRAM_BOT_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_MODE", "polling")

    from app.config import get_settings

    get_settings.cache_clear()
    await bot_setup.clear_webhook_for_polling(get_settings())
    assert deleted["called"] is True

    bot_setup._bot = None
    get_settings.cache_clear()
