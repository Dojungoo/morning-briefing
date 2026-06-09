"""add briefings.status (generation lifecycle)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-09 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing rows are completed briefings → default them to "ready".
    op.add_column(
        "briefings",
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="ready",
        ),
    )


def downgrade() -> None:
    op.drop_column("briefings", "status")
