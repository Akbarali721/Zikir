"""Telegram chat id and daily reminder opt-in

Revision ID: 007_user_reminders
Revises: 006_leaderboard_opt_in
Create Date: 2026-04-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_user_reminders"
down_revision: Union[str, None] = "006_leaderboard_opt_in"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "users",
        sa.Column("reminder_opt_in", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("users", sa.Column("reminder_last_morning_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("reminder_last_evening_date", sa.Date(), nullable=True))
    op.create_index("ix_users_telegram_chat_id", "users", ["telegram_chat_id"], unique=False)
    op.alter_column("users", "reminder_opt_in", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_users_telegram_chat_id", table_name="users")
    op.drop_column("users", "reminder_last_evening_date")
    op.drop_column("users", "reminder_last_morning_date")
    op.drop_column("users", "reminder_opt_in")
    op.drop_column("users", "telegram_chat_id")
