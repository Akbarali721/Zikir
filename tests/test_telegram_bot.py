import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_webhook_rejects_bad_secret(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("TELEGRAM_BOT_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "expected-secret")

    from app.config import get_settings

    get_settings.cache_clear()

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/telegram/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        )
        assert r.status_code == 403

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_webhook_requires_secret(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("TELEGRAM_BOT_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "")

    from app.config import get_settings

    get_settings.cache_clear()

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/telegram/webhook", json={"update_id": 1})
        assert r.status_code == 503

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_webhook_disabled_without_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_BOT_ENABLED", "true")

    from app.config import get_settings

    get_settings.cache_clear()

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/telegram/webhook", json={"update_id": 1})
        assert r.status_code == 503

    get_settings.cache_clear()


def test_welcome_text_uzbek():
    from app.bot.handlers import WELCOME_TEXT

    assert "Assalomu alaykum" in WELCOME_TEXT
    assert "Million Istig‘for" in WELCOME_TEXT
