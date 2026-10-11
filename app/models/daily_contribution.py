from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserDailyContribution(Base):
    """Kunlik hissa (DISPLAY_TIMEZONE bo‘yicha). Yangi yozuvlar sync vaqtida to‘ldiriladi."""

    __tablename__ = "user_daily_contributions"
    __table_args__ = (UniqueConstraint("user_id", "local_date", name="uq_user_daily_local_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    dhikr: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    active_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
