from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GlobalProgress(Base):
    __tablename__ = "global_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_dhikr_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_active_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    dhikr_goal: Mapped[int] = mapped_column(Integer, default=1_000_000, server_default="1000000", nullable=False)
    seconds_goal: Mapped[int] = mapped_column(Integer, default=1_000_000, server_default="1000000", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
