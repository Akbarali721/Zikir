import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


pytestmark = pytest.mark.asyncio

requires_pg = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL") and "postgresql" not in os.getenv("DATABASE_URL", ""),
    reason="PostgreSQL kerak",
)


@requires_pg
async def test_new_user_auto_onboarded_without_profile_form():
    app = create_app()
    headers = {"X-Test-Telegram-Id": "8800112233"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        me = (await client.get("/api/me", headers=headers)).json()
        assert me["onboarding_completed"] is True
        assert me["display_name"]
        assert me["user"]["telegram_id"] == 8800112233

