"""Central registry: import all ORM models so Alembic autogenerate sees them.

When adding a feature module with models.py, import it here — do not rely on
side effects from other modules.
"""

from app.modules.analysis.models import (
    Analysis,
    DetectedSubscription,
    Recommendation,
)
from app.modules.auth.models import User
from app.modules.statements.models import Statement, Transaction

__all__ = [
    "User",
    "Statement",
    "Transaction",
    "Analysis",
    "DetectedSubscription",
    "Recommendation",
]
