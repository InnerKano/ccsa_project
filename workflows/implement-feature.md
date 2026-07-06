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

**When a feature must absorb real-world variability** (many input formats, providers, locales), isolate that behind a small pluggable sub-package with a base contract + a registry, so new variants are added without touching `api.py`. Example: `modules/statements/ingest/` (`base.py` contracts → `delimited.py` implementation → `registry.py` selection). This keeps the controller thin and the feature open to extension (see `DECISIONS.md` D15). Do not over-abstract when there is only one format — introduce the seam when the second variant appears.

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

Frontend code follows `ARCHITECTURE.md`: **Next.js App Router**, **Tailwind CSS** (v4, tokens in `app/globals.css`), **React Context** for session state, **SWR** for authenticated reads. Transport stays in `lib/api/`; UI primitives in `components/ui/`; feature screens in `app/`.

**Before building any screen or component, read [`frontend/DESIGN.md`](../frontend/DESIGN.md)** — it is the source of truth for tokens, component usage, layout shells, and the required loading/empty/error states. New UI must be consistent with it; if you change the design language, update `DESIGN.md` in the same commit.

**Layering (do not bypass):**

```
app/<route>/page.tsx              → thin route shell (RequireAuth + AppShell + feature view)
components/<feature>/             → feature UI (StatementUploadForm, StatementList, AnalysisDetailView, …)
components/layout/ + auth/        → AppShell, AuthLayout, RequireAuth, GuestOnly
components/ui/                    → reusable primitives (Button, Field, Card, Alert, …)
lib/api/<feature>.ts              → typed calls built on apiFetch (one module per backend feature)
lib/api/client.ts                 → apiFetch + ApiError (Bearer token, JSON/FormData, {detail} errors)
lib/auth/session.ts               → token read/write (single persistence seam)
lib/auth/context.tsx              → AuthProvider / useAuth (UI session state)
lib/format.ts                     → formatCurrency / formatDate (Decimal strings from API)
frontend/DESIGN.md                → visual/UX source of truth (read before any new screen)
```

**Typed API call** (feature modules use the shared client — not raw `fetch` with a manual token):

```typescript
// frontend/lib/api/statements.ts
import { apiFetch } from "@/lib/api/client";

export type StatementSummary = {
  id: string;
  filename: string;
  currency: string;
  transaction_count: number;
  uploaded_at: string;
};

export function uploadStatement(file: File, currency = "USD"): Promise<StatementSummary> {
  const form = new FormData();
  form.append("file", file);
  form.append("currency", currency);
  return apiFetch<StatementSummary>("/api/statements", { method: "POST", body: form });
}
```

**SWR reads** — use a **named cache key** plus an explicit fetcher from `lib/api/` (dashboard pattern):

```typescript
import useSWR from "swr";
import { listStatements } from "@/lib/api/statements";

const { data, error, isLoading, mutate } = useSWR("statements", listStatements);
```

The default fetcher in `app/providers.tsx` is `(path) => apiFetch(path)` — suitable when the key is an API path (e.g. `useSWR("/api/analysis", () => apiFetch("/api/analysis"))`). Prefer named keys (`"statements"`, `"analyses"`, `analysis-${id}`) when the fetcher is a typed helper. Invalidate with `mutate("statements")` after uploads or writes.

**A4 sub-phases:** the full frontend vertical slice ships as **A4.1 → A4.6** (see `middle-phases.md`) — one commit per sub-phase, each leaving something verifiable in the browser. Mapping:

| Sub | Delivers |
|---|---|
| A4.1 | CORS, Tailwind tokens, `components/ui/`, `apiFetch`, `AuthProvider`, Compose `npm install` on frontend startup |
| A4.2 | Login/register/landing, `RequireAuth`/`GuestOnly`, `AppShell` |
| A4.3 | `lib/api/statements.ts`, `/upload` |
| A4.4 | `lib/api/analysis.ts`, `/dashboard` (list + run analysis) |
| A4.5 | `/analysis/[id]` full breakdown (`components/analysis/`) |
| A4.6 | Docs closeout — workflows/READMEs aligned with reality |

**Frontend-only features** (no new backend module): skip Steps 2–4. Start at Step 1 (contract in `API.md` already exists), then Step 5, Step 6, Step 8. Example: A4.3–A4.5.

**Money on the wire:** backend serializes `Decimal` fields as JSON strings (`API.md`). Parse with `Number()` only at display time via `lib/format.ts` — never use JS `float` for calculations in the UI.

## Step 6: Test end-to-end

The canonical manual check for any feature (the "did this commit actually work?" pass):

1. Rebuild and start the stack from the repo root: `docker compose up --build`.
2. Open the feature at http://localhost:3000 and exercise the happy path in the browser.
3. Verify persistence in the DB: `docker compose exec db psql -U postgres -d ccsa`.

**Frontend dependency changes** (new `npm` package in `package.json`): the frontend's
`node_modules` lives in a **named volume** (`frontend_node_modules`), isolated from the host,
so it survives `--build` and does **not** auto-refresh when `package.json` changes. The compose
`frontend` service runs `npm install && npm run dev` on startup for exactly this reason, so
`docker compose up --build` is enough. If the stack is already running and you just added a dep,
sync it without a full rebuild:

```bash
docker compose exec frontend npm install
docker compose restart frontend   # next dev caches module resolution; restart to pick it up
```

A `500` with `Cannot find module '<pkg>'` in the frontend logs is always this: the container's
volume is behind `package.json`. It is never fixed by editing code.

**Phase A browser happy path** (after A4 — full MVP, no LLM): with Compose running at http://localhost:3000:

1. Register a new account (or log in).
2. **Upload** → choose `backend/fixtures/sample.csv` → submit.
3. **Dashboard** → confirm the statement appears → **Run analysis**.
4. **Results** (`/analysis/{id}`) → confirm subscriptions (e.g. NETFLIX, SPOTIFY, AMAZON PRIME), recommendations, and savings totals.
5. **Sign out** → **Sign in** → **Dashboard** → **View results** on the same statement (persistence, D6).
6. Optional DB check: `docker compose exec db psql -U postgres -d ccsa -c "SELECT id FROM analyses LIMIT 3;"`

Layer 2 (LLM) is not required for this path (`ai_enabled: false` in the MVP).

## Step 7: Quick quality pass

```bash
docker compose exec backend black app
cd frontend && npm run lint
```

Do not block the feature on minor warnings — prioritize working and tested code. Security issues (Red zone in `AI_RULES.md`) do block.

## Step 8: Documentation

- Update `docs/API.md` with the new endpoint (same format: no envelope, standard status codes). For A4.1-style cross-cutting changes, document CORS in `API.md` instead of inventing a new doc.
- If AI contributed something non-trivial (Yellow/Red), add a line to `docs/AI_LOG.md` — see format in `AI_RULES.md`.
- Update `workflows/middle-phases.md` Status (and sub-phase checkboxes for A4) when a delivery lands.
- **Frontend changes:** follow [`frontend/DESIGN.md`](../frontend/DESIGN.md); update it if the design language changes. Keep `frontend/lib/README.md` and `frontend/components/README.md` accurate when adding API modules or component folders.

## Step 9: Commit

One commit per feature, with a descriptive **imperative** summary (matches the repo history — no `feat(scope):` prefix):

```bash
git add .
git commit -m "Add statements module (CSV upload + parse endpoint)"
```

---

## Checklist

- [ ] Data model and API contract defined before coding
- [ ] Migration created, reviewed by hand, applied (backend features only)
- [ ] Feature lives entirely in `modules/<feature>/` (nothing loose in flat folders)
- [ ] At least one test covers the happy path (backend); frontend: manual Phase A path or sub-phase path
- [ ] End-to-end flow tested manually (`docker compose up --build` → browser)
- [ ] `API.md` updated (backend); `frontend/DESIGN.md` followed (frontend)
- [ ] `AI_LOG.md` updated if applicable
- [ ] `middle-phases.md` Status updated when a phased delivery lands
- [ ] Commit with a descriptive imperative message (e.g. `Add <feature> module ...`)

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
