# statements

**Endpoints:** `POST/GET /api/statements`, `GET/DELETE /api/statements/{id}`, `POST /{id}/restore`, `DELETE /{id}/permanent` (`docs/API.md`)

**Models:** `Statement`, `Transaction` (`docs/DATA_MODEL.md`)

**Depends on:** `auth` (JWT, per-user isolation via `get_current_user`)

**Key rule (D4):** parse the upload in memory; do not persist raw files — only normalized transactions.

**Accepted inputs:** delimited exports (`.csv`, `.tsv`, `.txt`) and bank/card statement PDFs (`.pdf`). Same API, same persistence path.

**Ingestion (`ingest/`, D15 + D18 + D19):** pluggable parser pipeline. Format adapters extract rows; shared column mapping normalizes fields. New layouts plug into the registry / PDF profiles without touching `api.py`.

- `base.py` — contracts (`StatementParser`, `ParseOptions`, `ParsedTransaction`, `IngestError`).
- `columns.py` — shared header vocabulary, column plan, tabular row → normalized transactions (CSV and PDF).
- `normalizers.py` — encoding fallback, date (ISO / DD-MM / MM-DD / EN+ES month names), amount (US/EU, signs, debit-credit).
- `delimited.py` — CSV/TSV parser with delimiter sniffing + EN/ES column inference.
- `pdf/` — PDF adapter (D18): `parser.py`, `extract.py` (pdfplumber), `detect.py`, `lines.py`.
- `pdf/profiles/` — per-bank row profiles (D19): generic/card, Capital One 360, PNC; add a profile file for a new layout.
- `registry.py` — selects a parser (PDF before delimited so binary bytes are not mis-read as CSV).

**Archive (D22):** `DELETE /{id}` soft-archives (`deleted_at`); `POST /{id}/restore` undoes; `DELETE /{id}/permanent` hard-deletes. Owner list/detail queries hide archived statements.

**Fixtures (synthetic, PII-free):** `backend/fixtures/sample.csv`, `sample_es.csv`, and `fixtures/samples/caso1–4…`. Real bank files stay under git-ignored `fixtures/real_samples/` (never commit PII).

**OCR for scanned PDFs:** out of scope (Won't Have) — supported PDFs are text-based layouts.
