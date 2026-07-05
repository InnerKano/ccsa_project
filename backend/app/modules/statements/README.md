# statements (planned)

**Endpoints:** `POST/GET/DELETE /api/statements`, `GET /api/statements/{id}` (`docs/API.md`)

**Models:** `Statement`, `Transaction` (`docs/DATA_MODEL.md`)

**Depends on:** `auth` (JWT, per-user isolation)

**Key rule (D4):** parse CSV in memory; do not persist raw files.
