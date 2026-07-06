# statements

**Endpoints:** `POST/GET/DELETE /api/statements`, `GET /api/statements/{id}` (`docs/API.md`)

**Models:** `Statement`, `Transaction` (`docs/DATA_MODEL.md`)

**Depends on:** `auth` (JWT, per-user isolation via `get_current_user`)

**Key rule (D4):** parse CSV in memory; do not persist raw files.

**Ingestion (`ingest/`, D15):** pluggable parser pipeline.
- `base.py` — contracts (`StatementParser`, `ParseOptions`, `ParsedTransaction`, `IngestError`).
- `normalizers.py` — encoding fallback, date (ISO / DD-MM / MM-DD / EN+ES month names), amount (US/EU, signs, debit-credit).
- `delimited.py` — CSV/TSV parser with delimiter sniffing + EN/ES column inference.
- `registry.py` — selects a parser; **new formats (PDF dump, per-bank profiles) plug in here** without touching `api.py`.

**Fixtures (synthetic, PII-free — A5):** `backend/fixtures/sample.csv` (US) and `sample_es.csv` (LatAm/ES). Real statements must never be committed (`.gitignore` blocks `*.csv` except these two).
