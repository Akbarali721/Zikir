import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


pytestmark = pytest.mark.asyncio

requires_pg = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL") and "postgresql" not in os.getenv("DATABASE_URL", ""),
    reason="PostgreSQL kerak",
)


@requires_pg
async def test_me_and_sync_personal_counts_align():
    app = create_app()
    headers = {"X-Dev-Mode": "1"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        me0 = (await client.get("/api/me", headers=headers)).json()
        assert me0["onboarding_completed"] is True

        start = await client.post(
            "/api/session/start",
            headers=headers,
            json={"mode": "tap", "challenge": "million_istighfor"},
        )
        session_id = start.json()["session_id"]
        batch_id = str(uuid.uuid4())
        sync = await client.post(
            "/api/tasbeh/sync",
            headers=headers,
            json={
                "session_id": session_id,
                "dhikr_delta": 4,
                "active_seconds_delta": 2,
                "batch_id": batch_id,
            },
        )
        assert sync.status_code == 200
        me1 = (await client.get("/api/me", headers=headers)).json()
        assert me1["personal_dhikr_count"] == sync.json()["personal_dhikr_count"]
        assert me1["today"]["dhikr"] >= 4
