"""sync idempotency, visits, daily contributions, active session constraint

Revision ID: 004_sync_visits_admin
Revises: 003_user_retention_fields
Create Date: 2026-04-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_sync_visits_admin"
down_revision: Union[str, None] = "003_retention"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_dhikr_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "tasbeh_sync_batches",
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("dhikr_delta", sa.Integer(), nullable=False),
        sa.Column("active_seconds_delta", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["tasbeh_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("batch_id"),
    )
    op.create_index("ix_tasbeh_sync_batches_user_id", "tasbeh_sync_batches", ["user_id"])

    op.create_table(
        "user_visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_route", sa.String(length=64), nullable=True),
        sa.Column("first_dhikr_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_dhikr_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_visits_user_id", "user_visits", ["user_id"])
    op.create_index("ix_user_visits_last_seen_at", "user_visits", ["last_seen_at"])

    op.create_table(
        "user_daily_contributions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("dhikr", sa.Integer(), server_default="0", nullable=False),
        sa.Column("active_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "local_date", name="uq_user_daily_local_date"),
    )
    op.create_index("ix_user_daily_contributions_user_id", "user_daily_contributions", ["user_id"])
    op.create_index("ix_user_daily_contributions_local_date", "user_daily_contributions", ["local_date"])

    op.execute(
        """
        CREATE UNIQUE INDEX uq_tasbeh_sessions_one_active_per_user
        ON tasbeh_sessions (user_id)
        WHERE is_active = true
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_tasbeh_sessions_one_active_per_user")
    op.drop_table("user_daily_contributions")
    op.drop_index("ix_user_visits_last_seen_at", table_name="user_visits")
    op.drop_index("ix_user_visits_user_id", table_name="user_visits")
    op.drop_table("user_visits")
    op.drop_index("ix_tasbeh_sync_batches_user_id", table_name="tasbeh_sync_batches")
    op.drop_table("tasbeh_sync_batches")
    op.drop_column("users", "last_dhikr_at")
