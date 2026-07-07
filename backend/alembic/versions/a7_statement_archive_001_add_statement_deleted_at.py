"""Add deleted_at (soft archive) to statements (D22)

Revision ID: a7_statement_archive_001
Revises: a6_reco_kind_001
Create Date: 2026-07-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7_statement_archive_001"
down_revision: Union[str, None] = "a6_reco_kind_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable, no default: existing statements stay active (deleted_at IS NULL).
    # Indexed because every owner-facing statements/analysis query filters on it.
    op.add_column(
        "statements",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_statements_deleted_at"), "statements", ["deleted_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_statements_deleted_at"), table_name="statements")
    op.drop_column("statements", "deleted_at")
