# Workflow: Implement a Feature

Use each time you build a feature end-to-end. **Prerequisite:** bootstrap complete (Steps 1–5 in `start-project.md`) — Compose running, Alembic wired, structure validated.

Follow the UI → API → DB flow defined in `workflows/start-project.md`.

## Step 1: Plan (no code yet)

- What does the user need? Input/output? Edge cases? Validation?
- Design the data model and API contract before writing anything.

```json
// Example: upload statement
POST /api/statements
multipart/form-data: file=<csv>

// Response (no envelope — see API.md)
201 Created
{ "id": "uuid", "filename": "march.csv", "transaction_count": 42, "uploaded_at": "2026-07-04T00:00:00Z" }
```

## Step 2: Migration

Register the model in `app/core/models.py` first (Alembic autogenerate only sees imported models):

```python
# app/core/models.py
from app.modules.auth.models import User  # example
```

Then create and review the migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "Add statements tables"
```

If the endpoint accepts `UploadFile` / `Form(...)`, add `python-multipart` to `backend/requirements.txt` (required by FastAPI for multipart uploads).

Review the generated file by hand — check `nullable`, defaults, and that `downgrade()` actually reverses `upgrade()` (`AI_RULES.md`, Yellow zone).

```bash
docker compose exec backend alembic upgrade head
```

## Step 3: Backend — everything inside the feature module

```
backend/app/modules/statements/
├── models.py
├── schemas.py
├── api.py
└── services.py       # only if logic is non-trivial; omit for direct CRUD
```

**models.py**
```python
from sqlalchemy import Column, String, UUID, DateTime, Numeric
from datetime import datetime
from app.core.database import Base

class Statement(Base):
    __tablename__ = "statements"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, nullable=False)
    filename = Column(String, nullable=False)
    currency = Column(String, default="USD")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
```

**schemas.py**
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class StatementResponse(BaseModel):
    id: UUID
    filename: str
    currency: str
    transaction_count: int
    uploaded_at: datetime
```

**api.py**
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.statements.schemas import StatementResponse

router = APIRouter(prefix="/api/statements", tags=["statements"])

@router.post("/", response_model=StatementResponse, status_code=201)
async def upload_statement(file: UploadFile, db=Depends(get_db), user=Depends(get_current_user)):
    try:
        # parse CSV in memory; persist normalized transactions only
        ...
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

Register the new router in `main.py`.

## Step 4: Backend tests

```python
# backend/app/modules/statements/tests/test_statements_api.py
# Use a unique basename per module (e.g. test_statements_api.py) — not test_api.py in every module,
# or pytest raises "import file mismatch" when collecting app/modules/*/tests/.
def test_upload_statement(client, auth_headers):
    with open("fixtures/sample.csv", "rb") as f:
        response = client.post("/api/statements", files={"file": f}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["transaction_count"] > 0
```

```bash
docker compose exec backend pytest
```

Integration tests under `app/modules/<feature>/tests/` require Postgres with migrations applied; they skip automatically when the DB is unavailable (e.g. venv-only runs still execute structure/health tests).

## Step 5: Frontend

```typescript
// frontend/lib/api/statements.ts
export async function uploadStatement(file: File, token: string) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/statements`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) throw new Error((await res.json()).detail);
  return res.json();
}
```

## Step 6: Test end-to-end

1. `docker-compose up`
2. Use the feature from http://localhost:3000
3. Verify in DB: `docker-compose exec db psql -U postgres -d ccsa`

## Step 7: Quick quality pass

```bash
docker-compose exec backend black app
cd frontend && npm run lint
```

Do not block the feature on minor warnings — prioritize working and tested code. Security issues (Red zone in `AI_RULES.md`) do block.

## Step 8: Documentation

- Update `docs/API.md` with the new endpoint (same format: no envelope, standard status codes).
- If AI contributed something non-trivial (Yellow/Red), add a line to `docs/AI_LOG.md` — see format in `AI_RULES.md`.

## Step 9: Commit

```bash
git add .
git commit -m "feat(statements): add CSV upload and parse endpoint"
```

---

## Checklist

- [ ] Data model and API contract defined before coding
- [ ] Migration created, reviewed by hand, applied
- [ ] Feature lives entirely in `modules/<feature>/` (nothing loose in flat folders)
- [ ] At least one test covers the happy path
- [ ] End-to-end flow tested manually
- [ ] `API.md` updated
- [ ] `AI_LOG.md` updated if applicable
- [ ] Commit with descriptive message (`feat(scope): what`)

## Common patterns

**Errors:**
```python
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail="Internal error")
```

**Sensitive data:** never log or return raw CSV content or full transaction descriptions in error messages.
