# auth

**Endpoints:** `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password` (`docs/API.md`)

**Models:** `User` → `users` table (`docs/DATA_MODEL.md`)

**Files:**

| File | Role |
|---|---|
| `models.py` | `User` ORM |
| `schemas.py` | Register/login/forgot/reset request + response |
| `password_policy.py` | NIST-aligned strength rules (D24) — shared by register + reset; mirrored in frontend `lib/auth/passwordPolicy.ts` |
| `services.py` | Register, authenticate (email lowercase, D8), request/reset password (D23) |
| `api.py` | HTTP routes |
| `tests/test_api.py` | Register/login integration tests (Postgres + migration) |
| `tests/test_password_reset.py` | Recovery flow + password policy tests |

**Cross-cutting:** password hashing + JWT + reset-token helpers (`create_password_reset_token`, `read_reset_token_subject`, `verify_password_reset_token`) + `get_current_user` live in `app/core/security.py`. Email delivery is `app/shared/email/` (provider-agnostic, D23).

**Password recovery (D23):** stateless JWT bound to the user's `password_hash` (single-use, self-invalidating, **no token table / no migration**). `forgot-password` never reveals whether an email exists; `reset-password` returns a generic error and forces re-login.

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
