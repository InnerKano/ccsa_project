"""Add kind column to recommendations (fee vs subscription savings, D21)

Revision ID: a6_reco_kind_001
Revises: a3_analysis_001
Create Date: 2026-07-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a6_reco_kind_001"
down_revision: Union[str, None] = "a3_analysis_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default backfills any pre-existing rows as subscription cancellations
    # (the only kind produced before D21); new rows always set kind explicitly.
    op.add_column(
        "recommendations",
        sa.Column(
            "kind",
            sa.String(length=32),
            nullable=False,
            server_default="cancel_subscription",
        ),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "kind")
