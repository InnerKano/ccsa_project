"""Add analyses, detected_subscriptions and recommendations tables

Revision ID: a3_analysis_001
Revises: a2_statements_001
Create Date: 2026-07-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3_analysis_001"
down_revision: Union[str, None] = "a2_statements_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("statement_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("ai_enabled", sa.Boolean(), nullable=False),
        sa.Column("layer_used", sa.String(length=16), nullable=False),
        sa.Column("monthly_recurring_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("estimated_savings", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analyses_statement_id"), "analyses", ["statement_id"], unique=False)
    op.create_index(op.f("ix_analyses_user_id"), "analyses", ["user_id"], unique=False)

    op.create_table(
        "detected_subscriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("analysis_id", sa.UUID(), nullable=False),
        sa.Column("merchant", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("cadence", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_detected_subscriptions_analysis_id"),
        "detected_subscriptions",
        ["analysis_id"],
        unique=False,
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("analysis_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.String(length=1024), nullable=False),
        sa.Column("estimated_saving", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_recommendations_analysis_id"),
        "recommendations",
        ["analysis_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendations_analysis_id"), table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index(
        op.f("ix_detected_subscriptions_analysis_id"), table_name="detected_subscriptions"
    )
    op.drop_table("detected_subscriptions")
    op.drop_index(op.f("ix_analyses_user_id"), table_name="analyses")
    op.drop_index(op.f("ix_analyses_statement_id"), table_name="analyses")
    op.drop_table("analyses")
