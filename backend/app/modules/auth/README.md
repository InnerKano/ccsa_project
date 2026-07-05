# auth

**Endpoints:** `POST /api/auth/register`, `POST /api/auth/login` (`docs/API.md`)

**Models:** `User` → `users` table (`docs/DATA_MODEL.md`)

**Files:**

| File | Role |
|---|---|
| `models.py` | `User` ORM |
| `schemas.py` | Register/login request/response |
| `services.py` | Register, authenticate (email lowercase per D8) |
| `api.py` | HTTP routes |
| `tests/test_api.py` | Integration tests (Postgres + migration) |

**Cross-cutting:** password hashing + JWT + `get_current_user` live in `app/core/security.py` (reused by statements/analysis).

**Migration:** `alembic/versions/a1_users_001_add_users_table.py` — first project revision.

**Zone:** Red (`docs/AI_RULES.md`) — review security code line by line before commit.

**Verify:**

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend pytest
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"securepassword123"}'
```

Frontend: `/login`, `/register` — `frontend/lib/api/auth.ts`
