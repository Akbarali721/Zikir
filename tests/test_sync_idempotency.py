import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.main import create_app
from app.models.sync_batch import TasbehSyncBatch


pytestmark = pytest.mark.asyncio

requires_pg = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL") and "postgresql" not in os.getenv("DATABASE_URL", ""),
    reason="PostgreSQL TEST_DATABASE_URL or DATABASE_URL kerak",
)


@requires_pg
async def test_sync_batch_idempotent():
    app = create_app()
    headers = {"X-Dev-Mode": "1"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        me = (await client.get("/api/me", headers=headers)).json()
        start = await client.post("/api/session/start", headers=headers, json={"mode": "tap"})
        assert start.status_code == 200
        session_id = start.json()["session_id"]
        batch_id = str(uuid.uuid4())
        body = {
            "session_id": session_id,
            "dhikr_delta": 3,
            "active_seconds_delta": 2,
            "batch_id": batch_id,
        }
        r1 = await client.post("/api/tasbeh/sync", headers=headers, json=body)
        assert r1.status_code == 200
        r2 = await client.post("/api/tasbeh/sync", headers=headers, json=body)
        assert r2.status_code == 200
        assert r1.json()["personal_dhikr_count"] == r2.json()["personal_dhikr_count"]

    async with AsyncSessionLocal() as session:
        count = await session.scalar(
            select(TasbehSyncBatch).where(TasbehSyncBatch.batch_id == uuid.UUID(batch_id))
        )
        assert count is not None
