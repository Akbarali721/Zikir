import os

import pytest

from app.models.user import User
from app.services.user_identity_service import preferred_display_name as public_display_name


def test_public_display_name_prefers_display_name():
    u = User(telegram_id=1, display_name="Akbar", first_name="Other", username="x")
    assert public_display_name(u) == "Akbar"


def test_public_display_name_username():
    u = User(telegram_id=1, display_name=None, first_name=None, username="ali")
    assert public_display_name(u) == "@ali"


requires_pg = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL") and "postgresql" not in os.getenv("DATABASE_URL", ""),
    reason="PostgreSQL kerak",
)


@pytest.mark.asyncio
@requires_pg
async def test_top10_respects_opt_in():
    from datetime import date, datetime, timezone

    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.models.daily_contribution import UserDailyContribution
    from app.services.daily_service import local_date_for_instant
    from app.services.leaderboard_service import get_top10_today
    from app.config import get_settings

    settings = get_settings()
    today = local_date_for_instant(datetime.now(timezone.utc), settings.display_timezone)
    tid = 9_001_002_003

    async with AsyncSessionLocal() as session:
        from app.services.telegram import get_or_create_user

        visible = await get_or_create_user(
            session,
            {"id": tid, "username": "top_visible", "first_name": "Ko'rinadi"},
        )
        hidden = await get_or_create_user(
            session,
            {"id": tid + 1, "username": "top_hidden", "first_name": "Yashirin"},
        )
        visible.leaderboard_opt_in = True
        visible.display_name = "Reytingda"
        hidden.leaderboard_opt_in = False

        from sqlalchemy.dialects.postgresql import insert as pg_insert

        for user, dhikr in ((visible, 100), (hidden, 999)):
            stmt = pg_insert(UserDailyContribution).values(
                user_id=user.id,
                local_date=today,
                dhikr=dhikr,
                active_seconds=10,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "local_date"],
                set_={"dhikr": dhikr, "active_seconds": 10},
            )
            await session.execute(stmt)
        await session.commit()

    async with AsyncSessionLocal() as session:
        top = await get_top10_today(session)
        names = [e.display_label for e in top]
        assert "Reytingda" in names
        assert not any("Yashirin" in n for n in names)

    async with AsyncSessionLocal() as session:
        await session.execute(
            UserDailyContribution.__table__.delete().where(
                UserDailyContribution.user_id.in_(
                    select(User.id).where(User.telegram_id.in_([tid, tid + 1]))
                )
            )
        )
        await session.commit()
