"""users.leaderboard_opt_in for TOP-10 visibility

Revision ID: 006_leaderboard_opt_in
Revises: 005_session_challenge
Create Date: 2026-04-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_leaderboard_opt_in"
down_revision: Union[str, None] = "005_session_challenge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("leaderboard_opt_in", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.alter_column("users", "leaderboard_opt_in", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "leaderboard_opt_in")
