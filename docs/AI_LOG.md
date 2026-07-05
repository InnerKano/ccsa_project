# AI Log

Record of AI usage in the project. This file is filled in whenever AI contributes something non-trivial (Yellow/Red zone or architectural decisions), according to the `AI_RULES.md` protocol.

It is the direct input for answering in the video: "where did AI help most? where did it fail?" with real evidence instead of memory.

## Format

```
YYYY-MM-DD | [module] | What was asked | Usefulness (1-5) | What was fixed manually
```

## Entries

| Date | Module | What was asked | Usefulness (1-5) | Manual correction |
|---|---|---|---|---|
| 2026-07-04 | architecture | Create the initial backend/frontend folder structure and decide which placeholder modules to keep | 4 | Kept the scaffold minimal and avoided premature feature-specific files; only the core structure and entrypoint were preserved. |
| 2026-07-04 | backend | Step 2.1 walking skeleton: FastAPI app, GET /health, requirements.txt, Dockerfile | 5 | No corrections needed; health endpoint matches API.md contract, no DB/CORS yet (deferred to Steps 3–4). |
| 2026-07-05 | backend | Add pytest health test + README run/test instructions | 5 | Clarified single test suite for venv and Docker; no duplicate e2e for Step 2.1. |
| 2026-07-05 | infra | Step 3 Docker Compose: backend + frontend + Postgres, core/config + database wiring | 5 | DB check on startup in Compose; SKIP_DB_CHECK for pytest/venv-only; no migrations yet (Step 4). |
| 2026-07-05 | database | Step 4 Alembic wiring: env.py, get_db(), core/models registry; no feature tables | 5 | First migration deferred to auth feature per DATA_MODEL.md; no empty revisions. |
| 2026-07-05 | architecture | Step 5 validate structure: module stubs, test_structure, docs alignment, D11 | 5 | ARCHITECTURE tree updated to match disk; bootstrap complete, next = auth. |

