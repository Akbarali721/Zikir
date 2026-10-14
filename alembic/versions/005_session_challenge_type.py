"""session challenge_type for 33 tasbeh vs million istighfor

Revision ID: 005_session_challenge
Revises: 004_sync_visits_admin
Create Date: 2026-04-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_session_challenge"
down_revision: Union[str, None] = "004_sync_visits_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasbeh_sessions",
        sa.Column(
            "challenge_type",
            sa.String(length=24),
            nullable=False,
            server_default="million_istighfor",
        ),
    )
    op.alter_column("tasbeh_sessions", "challenge_type", server_default=None)


def downgrade() -> None:
    op.drop_column("tasbeh_sessions", "challenge_type")
