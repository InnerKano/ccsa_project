# Project Scope — Credit Card Savings Analyzer (CCSA)

---

## General Project Scope

**Included by default:**
- Project structure (see `ARCHITECTURE.md`)
- Modular FastAPI backend + Next.js frontend
- Docker Compose for local development
- PostgreSQL + Alembic
- Basic JWT authentication (register/login)
- Auto-generated API documentation (`/docs`)
- Deployment configuration (Vercel + Railway/Render)

**Secondary feature list (optional, add if required):**
- OAuth / SSO
- RBAC or fine-grained permissions
- Advanced caching, message queues
- Microservices
- Advanced observability (APM, tracing)
- Multi-region / load balancing

## CCSA-specific Scope

---
### Problem

- What does it solve? Convert a card statement (CSV) into clear conclusions about recurring expenses and subscriptions, with an estimate of how much could be saved by cancelling unused items.
- Who uses it? An individual consumer who wants to understand and reduce fixed expenses. [Consider whether the target is an end user or someone analyzing data for clients.]
- Why is this viable in 72 hours and not an empty demo? Because the rules-based core (recurrence detection + savings estimate) already delivers real value on its own, without relying on perfect AI. It is a usable product, not just a prompt wrapper.

### Must Have

- **Auth:** register / login. Each user only sees their own data.
- **CSV upload:** upload a **delimited** transaction export (CSV/TSV) with column inference or explicit mapping (date, description, amount, or debit/credit), locale-aware parsing (EN/ES, US/EU number formats), and format validation. Raw PDF/statement dumps are out of MVP (D15, Could Have).
- **Parsing + rules-based categorization (Layer 1, no AI):** normalize transactions and classify by keywords/regex (e.g., "NETFLIX" → subscription/streaming).
- **Recurring/subscription detection:** identify merchants that repeat with stable amounts and cadence.
- **Estimated savings + basic recommendations:** monthly subscription totals and an actionable list ("cancel X ≈ save $Y/month"), computed by rules.
- **Persist analysis:** results are saved to the user's account and retrievable later.
- **Results dashboard:** upload screen + results screen (detected recurrents, totals, recommendations).

### Should Have

- **Layer 2 (LLM):** finer categorization and natural-language recommendations, with a **provider-agnostic** setup (Ollama local / OpenAI via `.env`) and **automatic fallback to Layer 1** on failure.
- **Example CSV** included in the repo for testing without real data.
- **Category summaries** (streaming, services, food, etc.) with aggregated amounts.
- **Detection of fees/commissions + savings recommendations** (overdraft, ATM, maintenance, annual… ). **Implemented — D21.** Fees are aggregated by type and counted as *hard* savings, separate from *potential* subscription savings; every recurring charge is surfaced (discretionary → cancel, essential → review). This closes the "commissions" half of the brief's problem statement.

### Could Have

- Automatic import via **Plaid** (instead of manual CSV upload). [Check feasibility with bank API keys.]
- **PDF parsing** of bank statements — and, related, parsing of PDF-exported-to-`.csv` statement dumps (fixed-width, multi-line, page noise). See D15: enabled by the pluggable `ingest/` design, deferred out of MVP.
- **Per-bank format profiles** (e.g. Banco de Bogotá, Cash App) as ingestion adapters.
- Month-over-month comparison and alerts for new subscriptions.
- ~~Detection of fees/charges in addition to subscriptions.~~ **Done — moved to Should Have (D21).**

Goal:
- **Automatic subscription cancellation** (the "nice-to-have" of the brief): this requires merchant integrations, per-service OAuth, and legal/operational implications. It is recommended as future work; cancellations should be performed by the user.

### Won't Have (explicit out-of-scope)

- **Plaid / bank aggregator production integration:** out of scope; input is CSV.
- **PDF parsing with OCR:** formats vary too much across banks for reliable implementation in the timeframe.
- **Multi-currency / currency conversion.** Only USD is supported for now. Limitation implemented in the frontend. on 
- **Mobile app / browser extension.**

### Known risks / assumptions

- Assume users can export CSV from their bank (most cases). If not, the project would be blocked until PDF parsing or Plaid import is available (Could Have).
- Assume volume is processable in memory (tens–hundreds of rows per statement).
- The quality of Layer 2 recommendations depends on the LLM provider; Layer 1 guarantees minimum value.

### Success criteria

- A new user can: register → upload an example CSV → see detected subscriptions and estimated savings → return later and find that analysis saved.
- All of the above works **even if Layer 2 (LLM) is disabled** (graceful degradation verified).
- No sensitive data is leaked: raw files are not persisted, transactions are not logged, and one user cannot see another's data.
