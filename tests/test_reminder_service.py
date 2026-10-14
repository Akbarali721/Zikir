from datetime import date

import pytest

from app.models.user import User
from app.services.reminder_service import process_evening_reminders, process_morning_reminders


class FakeSession:
    async def commit(self):
        pass


class FakeSessionMaker:
    async def __aenter__(self):
        return FakeSession()

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_morning_reminder_skips_duplicate_same_day(monkeypatch):
    sent = []

    async def fake_send(chat_id, text, parse_mode=None):
        sent.append(chat_id)

    user = User(
        id=1,
        telegram_id=10,
        telegram_chat_id=10,
        reminder_opt_in=True,
        reminder_last_morning_date=date(2026, 4, 15),
    )

    async def fake_users(_session):
        return [user]

    monkeypatch.setattr("app.services.reminder_service.users_due_for_reminders", fake_users)
    monkeypatch.setattr(
        "app.services.reminder_service.local_date_for_instant",
        lambda *_: date(2026, 4, 15),
    )
    monkeypatch.setattr("app.services.reminder_service.AsyncSessionLocal", FakeSessionMaker)

    n = await process_morning_reminders(fake_send)
    assert n == 0
    assert sent == []


@pytest.mark.asyncio
async def test_morning_reminder_sends_once(monkeypatch):
    sent = []

    async def fake_send(chat_id, text, parse_mode=None):
        sent.append(chat_id)

    user = User(
        id=1,
        telegram_id=10,
        telegram_chat_id=10,
        reminder_opt_in=True,
        reminder_last_morning_date=None,
    )

    async def fake_users(_session):
        return [user]

    monkeypatch.setattr("app.services.reminder_service.users_due_for_reminders", fake_users)
    monkeypatch.setattr(
        "app.services.reminder_service.local_date_for_instant",
        lambda *_: date(2026, 4, 16),
    )
    monkeypatch.setattr("app.services.reminder_service.AsyncSessionLocal", FakeSessionMaker)

    n = await process_morning_reminders(fake_send)
    assert n == 1
    assert sent == [10]
    assert user.reminder_last_morning_date == date(2026, 4, 16)


@pytest.mark.asyncio
async def test_evening_reminder_uses_today_dhikr(monkeypatch):
    sent = []

    async def fake_send(chat_id, text, parse_mode=None):
        sent.append((chat_id, text))

    user = User(
        id=1,
        telegram_id=10,
        telegram_chat_id=10,
        reminder_opt_in=True,
        reminder_last_evening_date=None,
        first_name="Test",
    )

    async def fake_users(_session):
        return [user]

    async def fake_today(_session, _uid):
        return (12, 60)

    monkeypatch.setattr("app.services.reminder_service.users_due_for_reminders", fake_users)
    monkeypatch.setattr(
        "app.services.reminder_service.local_date_for_instant",
        lambda *_: date(2026, 4, 16),
    )
    monkeypatch.setattr("app.services.reminder_service.get_today_from_daily", fake_today)
    monkeypatch.setattr("app.services.reminder_service.AsyncSessionLocal", FakeSessionMaker)

    n = await process_evening_reminders(fake_send)
    assert n == 1
    assert "12" in sent[0][1]
