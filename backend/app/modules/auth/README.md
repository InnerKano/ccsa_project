# auth (planned — first feature)

**Endpoints:** `POST /api/auth/register`, `POST /api/auth/login` (`docs/API.md`)

**Models:** `User` (`docs/DATA_MODEL.md` → `users` table)

**Files to create when implementing:**

- `models.py`, `schemas.py`, `api.py`, `services.py` (password hashing, JWT)
- `tests/test_api.py`
- First Alembic revision (ships with this module — see `workflows/implement-feature.md`)

**Zone:** Red (`docs/AI_RULES.md`) — review security code line by line.
