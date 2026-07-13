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

## Built modules (CCSA)

| Module | Status | Scope reference |
|---|---|---|
| [auth](./auth/README.md) | Built (A1) | Must Have — register/login, JWT, password recovery |
| [statements](./statements/README.md) | Built (A2 + A2.1 + D18/D19) | Must Have — upload & parse (CSV/TSV + PDF via `ingest/`); soft archive (D22) |
| [analysis](./analysis/README.md) | Built (A3, Layer 1) | Must Have — two-layer pipeline (Layer 2 → Phase B) |

**Module vs format:** PDF is not its own module. It is a second ingestion adapter under `statements/ingest/pdf/` that feeds the same `Statement` / `Transaction` models and API. New bank layouts are profile files, not new feature folders — see `statements/README.md` and `docs/DECISIONS.md` D15–D19.

See `docs/ARCHITECTURE.md` and `docs/DATA_MODEL.md` for entity mapping.
