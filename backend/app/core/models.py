"""Central registry: import all ORM models so Alembic autogenerate sees them.

When adding a feature module with models.py, import it here — do not rely on
side effects from other modules.
"""

from app.modules.auth.models import User

__all__ = ["User"]
