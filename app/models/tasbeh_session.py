from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TasbehSession(Base):
    __tablename__ = "tasbeh_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dhikr_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    active_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    challenge_type: Mapped[str] = mapped_column(
        String(24), default="million_istighfor", server_default="million_istighfor", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")  # noqa: F821
