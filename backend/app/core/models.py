"""Central registry: import all ORM models so Alembic autogenerate sees them.

When adding a feature module with models.py, import it here — do not rely on
side effects from other modules.

Example (auth feature — next step):
    from app.modules.auth.models import User
"""

# Models are registered as features land. No tables until the first feature migration.

__all__: list[str] = []
