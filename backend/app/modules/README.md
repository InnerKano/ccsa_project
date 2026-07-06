# Feature modules

Each business capability lives in its own folder under `modules/<feature>/`. Do not split by technical layer at the app root.

## Standard layout (per feature)

```
modules/<feature>/
├── api.py          # FastAPI router — HTTP only
├── models.py       # SQLAlchemy models
├── schemas.py      # Pydantic request/response shapes
├── services.py     # Business logic (omit if trivial CRUD)
└── tests/          # Happy-path API tests
```

## Registration checklist

1. Create the module folder and files above.
2. Import models in `app/core/models.py` (Alembic autogenerate).
3. Include router in `app/main.py`: `app.include_router(...)`.
4. Add migration via `implement-feature.md` Step 2.
5. Document endpoints in `docs/API.md`.

## Planned modules (CCSA)

| Module | Status | Scope reference |
|---|---|---|
| [auth](./auth/README.md) | Built (A1) | Must Have — register/login, JWT |
| [statements](./statements/README.md) | Built (A2 + A2.1) | Must Have — CSV upload & parse |
| [analysis](./analysis/README.md) | Built (A3, Layer 1) | Must Have — two-layer pipeline (Layer 2 → Phase B) |

See `docs/ARCHITECTURE.md` and `docs/DATA_MODEL.md` for entity mapping.
