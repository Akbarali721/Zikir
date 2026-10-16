"""Docker worker image: scripts yo‘q, kirish app.bot.worker."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_dockerignore_excludes_scripts():
    lines = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "scripts" in {line.strip() for line in lines if line.strip() and not line.strip().startswith("#")}


def test_main_dockerfile_does_not_copy_scripts():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY scripts" not in dockerfile


def test_worker_dockerfile_uses_app_module_entrypoint():
    dockerfile = (ROOT / "Dockerfile.worker").read_text(encoding="utf-8")
    assert "COPY app ./app" in dockerfile
    assert "app.bot.worker" in dockerfile
    assert "frontend-build" not in dockerfile


def test_scripts_module_not_importable_like_production_image(monkeypatch):
    """Production image kontekstida scripts/ yo‘q — faqat app/ bor."""
    import sys

    monkeypatch.delitem(sys.modules, "scripts", raising=False)
    monkeypatch.delitem(sys.modules, "scripts.run_telegram_bot_polling", raising=False)
    filtered = [p for p in sys.path if Path(p).resolve() != ROOT.resolve()]
    monkeypatch.setattr(sys, "path", filtered)
    with pytest.raises(ModuleNotFoundError, match="scripts"):
        __import__("scripts.run_telegram_bot_polling")


def test_worker_main_invokes_run_polling_without_network(monkeypatch):
    import asyncio

    import app.bot.worker as worker_mod
    from app.config import get_settings

    calls = {"polling": 0, "shutdown": 0}

    async def fake_run_polling(settings):
        calls["polling"] += 1
        assert settings.telegram_bot_mode == "polling"

    async def fake_shutdown():
        calls["shutdown"] += 1

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1:test")
    monkeypatch.setenv("TELEGRAM_BOT_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_MODE", "polling")
    get_settings.cache_clear()
    monkeypatch.setattr(worker_mod, "run_polling", fake_run_polling)
    monkeypatch.setattr(worker_mod, "shutdown_bot", fake_shutdown)

    asyncio.run(worker_mod._main())
    assert calls["polling"] == 1
    assert calls["shutdown"] == 1
    get_settings.cache_clear()
