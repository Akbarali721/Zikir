"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("personal_dhikr_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("personal_active_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    op.create_table(
        "global_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("total_dhikr_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_active_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("dhikr_goal", sa.Integer(), server_default="1000000", nullable=False),
        sa.Column("seconds_goal", sa.Integer(), server_default="1000000", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tasbeh_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dhikr_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("active_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasbeh_sessions_user_id"), "tasbeh_sessions", ["user_id"], unique=False)

    op.execute(
        sa.text(
            "INSERT INTO global_progress (total_dhikr_count, total_active_seconds, dhikr_goal, seconds_goal) "
            "VALUES (0, 0, 1000000, 1000000)"
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tasbeh_sessions_user_id"), table_name="tasbeh_sessions")
    op.drop_table("tasbeh_sessions")
    op.drop_table("global_progress")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
