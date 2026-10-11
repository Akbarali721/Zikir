"""user retention visit fields

Revision ID: 003_retention
Revises: 002_onboarding
Create Date: 2026-03-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_retention"
down_revision: Union[str, None] = "002_onboarding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_visit_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("global_dhikr_at_last_visit", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "global_dhikr_at_last_visit")
    op.drop_column("users", "last_visit_at")
