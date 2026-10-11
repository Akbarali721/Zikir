"""Asosiy bazadagi foydalanuvchi xulosasi (Akbarali va boshqalar) — deploy oldi tekshiruv."""
import asyncio

from sqlalchemy import select, func

from app.config import get_settings
from app.db.database import AsyncSessionLocal
from app.models.user import User


async def main():
    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(
                    User.display_name,
                    User.first_name,
                    User.personal_dhikr_count,
                    User.personal_active_seconds,
                    User.onboarding_completed,
                ).order_by(User.id)
            )
        ).all()
        total_d = await session.scalar(select(func.sum(User.personal_dhikr_count)))
        print(f"users={len(rows)} sum_personal_dhikr={total_d}")
        for r in rows:
            name = r.display_name or r.first_name or "—"
            if "akbar" in name.lower():
                print(
                    f"AKBARALI_SNAPSHOT name={name} dhikr={r.personal_dhikr_count} "
                    f"seconds={r.personal_active_seconds} onboarding={r.onboarding_completed}"
                )


if __name__ == "__main__":
    asyncio.run(main())
