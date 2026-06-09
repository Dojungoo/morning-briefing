"""initial schema: users + briefings

Revision ID: 0001
Revises:
Create Date: 2026-06-01 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "coders_id", sa.UUID(as_uuid=True), unique=True, nullable=False
        ),
        sa.Column("display_name", sa.String(64), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_coders_id", "users", ["coders_id"])

    op.create_table(
        "briefings",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "author_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("insight", sa.Text(), nullable=False),
        sa.Column("sections", JSONB(), nullable=False),
        sa.Column(
            "indicators",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "source_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("model", sa.String(64), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_briefings_author_id", "briefings", ["author_id"])
    op.create_index("ix_briefings_issue_date", "briefings", ["issue_date"])
    op.create_index("ix_briefings_created_at", "briefings", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_briefings_created_at", table_name="briefings")
    op.drop_index("ix_briefings_issue_date", table_name="briefings")
    op.drop_index("ix_briefings_author_id", table_name="briefings")
    op.drop_table("briefings")
    op.drop_index("ix_users_coders_id", table_name="users")
    op.drop_table("users")
