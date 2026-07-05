# Scripts

Optional utilities for local development. Nothing required here for the MVP bootstrap.

## Bootstrap verification (manual)

Run from the **repo root** after `docker compose up`:

```powershell
curl http://localhost:8000/health
docker compose exec db pg_isready -U postgres -d ccsa
docker compose exec backend alembic current
docker compose exec backend pytest
```

Automated layout checks live in `backend/tests/test_structure.py`. Compose mounts the full repo at `/workspace` (see `DECISIONS.md` D12) so the same tests pass inside Docker and on the host.

Add scripts here only when a command is repeated often enough to warrant automation (e.g. seed data, deploy helpers).
