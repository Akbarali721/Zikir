import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


pytestmark = pytest.mark.asyncio

requires_pg = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL") and "postgresql" not in os.getenv("DATABASE_URL", ""),
    reason="PostgreSQL TEST_DATABASE_URL or DATABASE_URL kerak",
)


@requires_pg
async def test_tasbeh_33_sync_does_not_increase_personal_or_global():
    app = create_app()
    headers = {"X-Dev-Mode": "1"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        progress_before = (await client.get("/api/progress", headers=headers)).json()
        me_before = (await client.get("/api/me", headers=headers)).json()
        personal_before = me_before["personal_dhikr_count"]
        global_before = progress_before["global"]["dhikr"]

        start = await client.post(
            "/api/session/start",
            headers=headers,
            json={"mode": "tap", "challenge": "tasbeh_33"},
        )
        assert start.status_code == 200
        assert start.json()["challenge_type"] == "tasbeh_33"
        session_id = start.json()["session_id"]

        body = {
            "session_id": session_id,
            "dhikr_delta": 5,
            "active_seconds_delta": 1,
            "batch_id": str(uuid.uuid4()),
        }
        sync = await client.post("/api/tasbeh/sync", headers=headers, json=body)
        assert sync.status_code == 200
        assert sync.json()["session_dhikr_count"] == 5
        assert sync.json()["personal_dhikr_count"] == personal_before

        progress_after = (await client.get("/api/progress", headers=headers)).json()
        assert progress_after["global"]["dhikr"] == global_before
