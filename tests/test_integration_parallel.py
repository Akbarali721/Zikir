"""PostgreSQL integration (test DB, X-Test-Telegram-Id). Production auth ishlatilmaydi."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration


def auth_headers(telegram_id: int) -> dict[str, str]:
    return {"X-Test-Telegram-Id": str(telegram_id)}


async def _global_totals(client: AsyncClient, headers: dict):
    r = await client.get("/api/progress", headers=headers)
    assert r.status_code == 200
    g = r.json()["global"]
    return g["dhikr"], g["active_seconds"], g["remaining_dhikr"], g["remaining_seconds"]


async def _user_sync_dhikr_and_time(client: AsyncClient, telegram_id: int, dhikr: int, seconds: int):
    h = auth_headers(telegram_id)
    batch_id = str(uuid.uuid4())
    t0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=telegram_id % 1000)
    t1 = t0 + timedelta(seconds=max(seconds + 5, 70))
    counter = {"t": t0}

    with patch("app.services.tasbeh_service._utcnow", side_effect=lambda: counter["t"]):
        await client.post("/api/session/stop", headers=h)
        start = await client.post("/api/session/start", headers=h, json={"mode": "tap"})
        assert start.status_code == 200, start.text
        sid = start.json()["session_id"]
        counter["t"] = t1
        sync = await client.post(
            "/api/tasbeh/sync",
            headers=h,
            json={
                "session_id": sid,
                "dhikr_delta": dhikr,
                "active_seconds_delta": seconds,
                "batch_id": batch_id,
            },
        )
    assert sync.status_code == 200, sync.text
    return batch_id, sync.json()


@pytest.mark.asyncio
async def test_integration_suite(integration_app):
    """Bitta event loop ichida barcha integratsion tekshiruvlar."""
    transport = ASGITransport(app=integration_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dev_mode = await client.get("/api/me", headers={"X-Dev-Mode": "1"})
        assert dev_mode.status_code == 401

        tid_onboard = 900_200
        h_on = auth_headers(tid_onboard)
        me = await client.get("/api/me", headers=h_on)
        assert me.status_code == 200
        if not me.json()["onboarding_completed"]:
            prof = await client.post(
                "/api/profile/onboarding",
                headers=h_on,
                json={"display_name": "Test Dev", "age": 25},
            )
            assert prof.status_code == 200
        assert (await client.get("/api/me", headers=h_on)).json()["onboarding_completed"]

        observer_id = 900_000_001
        obs_h = auth_headers(observer_id)
        await client.get("/api/me", headers=obs_h)
        before = await _global_totals(client, obs_h)

        for tid in range(900_001, 900_016):
            await _user_sync_dhikr_and_time(client, tid, 40, 60)

        after = await _global_totals(client, obs_h)
        assert after[0] - before[0] == 600
        assert after[1] - before[1] == 900
        assert before[2] - after[2] == 600
        assert before[3] - after[3] == 900

        tid = 900_100
        h = auth_headers(tid)
        await client.get("/api/me", headers=h)
        base_personal = (await client.get("/api/me", headers=h)).json()["personal_dhikr_count"]
        start = await client.post("/api/session/start", headers=h, json={"mode": "tap"})
        sid = start.json()["session_id"]
        batch_id = str(uuid.uuid4())
        body = {"session_id": sid, "dhikr_delta": 5, "active_seconds_delta": 3, "batch_id": batch_id}
        t0 = datetime(2026, 2, 1, tzinfo=timezone.utc)
        counter = {"t": t0}
        with patch("app.services.tasbeh_service._utcnow", side_effect=lambda: counter["t"]):
            await client.post("/api/tasbeh/sync", headers=h, json=body)
            counter["t"] = t0 + timedelta(seconds=10)
            await client.post("/api/tasbeh/sync", headers=h, json=body)
        assert (await client.get("/api/me", headers=h)).json()["personal_dhikr_count"] == base_personal + 5

        s1 = await client.post("/api/session/start", headers=auth_headers(900_102), json={"mode": "tap"})
        s2 = await client.post("/api/session/start", headers=auth_headers(900_102), json={"mode": "tap"})
        assert s1.json()["session_id"] == s2.json()["session_id"]

        assert (await client.get("/api/admin/overview", headers=auth_headers(900_001))).status_code == 403
        admin = await client.get("/api/admin/overview", headers=auth_headers(900_000_001))
        assert admin.status_code == 200
        assert admin.json()["total_users"] >= 16
