"""Analysis orchestration — runs Layer 1, persists results, enforces isolation.

This module owns *what gets persisted* and *per-user scoping*; the detection
logic lives in the pure ``rules`` package. Layer 2 (LLM) is intentionally not
implemented here yet (Phase B). The seam below shows exactly where it plugs in
with graceful fallback (D2): if/when an LLM enrichment is added, it wraps the
Layer 1 result and only upgrades ``ai_enabled``/``layer_used`` on success —
Layer 1 remains the guaranteed output.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.analysis.models import (
    Analysis,
    DetectedSubscription,
    Recommendation,
)
from app.modules.analysis.rules.engine import RulesResult, run_layer_one
from app.modules.auth.models import User
from app.modules.statements.services import get_statement_for_user


def run_analysis_for_statement(
    db: Session, user: User, statement_id: UUID
) -> Analysis | None:
    """Analyze a statement the user owns. Returns None if it is not theirs (→ 404).

    Per D10, this appends a new Analysis row on every call; previous runs are kept.
    """
    statement = get_statement_for_user(db, statement_id, user.id)
    if statement is None:
        return None

    transactions = list(statement.transactions)
    result: RulesResult = run_layer_one(transactions)

    # --- Layer 2 (LLM) seam — Phase B, D2 ---------------------------------
    # result = enrich_with_llm(result, transactions)  # only on success
    ai_enabled = False
    layer_used = "rules"
    # ----------------------------------------------------------------------

    for tx, category in zip(transactions, result.categories):
        tx.category = category

    analysis = Analysis(
        statement_id=statement.id,
        user_id=user.id,
        ai_enabled=ai_enabled,
        layer_used=layer_used,
        monthly_recurring_total=result.monthly_recurring_total,
        estimated_savings=result.estimated_savings,
    )
    db.add(analysis)
    db.flush()

    for sub in result.subscriptions:
        db.add(
            DetectedSubscription(
                analysis_id=analysis.id,
                merchant=sub.merchant,
                amount=sub.amount,
                cadence=sub.cadence,
                category=sub.category,
            )
        )
    for rec in result.recommendations:
        db.add(
            Recommendation(
                analysis_id=analysis.id,
                title=rec.title,
                detail=rec.detail,
                estimated_saving=rec.estimated_saving,
            )
        )

    db.commit()
    db.refresh(analysis)
    return analysis


def list_analyses_for_user(db: Session, user_id: UUID) -> list[Analysis]:
    return (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .all()
    )


def get_analysis_for_user(db: Session, analysis_id: UUID, user_id: UUID) -> Analysis | None:
    return (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == user_id)
        .first()
    )
