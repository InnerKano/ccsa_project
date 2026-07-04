# Engineering Decisions — Credit Card Savings Analyzer (CCSA)

This document captures key architectural and technical decisions. The first part lists default choices inherited from the starter kit; the second part contains CCSA-specific decisions that deviate from or extend those defaults.

## Technology Choices (starter kit defaults)

### FastAPI for Backend
**Decision**: Use FastAPI instead of Django or Flask

**Rationale**:
- Fast async support out of the box
- Excellent auto-generated API documentation
- Type hints reduce bugs
- Great for building APIs quickly
- Easy dependency injection

### Next.js for Frontend
**Decision**: Use Next.js instead of Create React App

**Rationale**:
- Built-in routing
- API routes capability
- Server-side rendering option
- Great developer experience
- Easy deployment to Vercel

### PostgreSQL for Database
**Decision**: Use PostgreSQL for relational data

**Rationale**:
- Industry standard
- Strong ACID guarantees
- Rich query language
- Good integration with Python/Node ecosystems
- Widely supported hosting

### Docker for Development
**Decision**: Use Docker Compose for local development

**Rationale**:
- Consistent environment across team
- Close to production environment
- Easy onboarding for new developers
- Service isolation
- Simple CI/CD integration

## Architectural Decisions

### Monorepo Structure
**Decision**: Keep frontend and backend in the same repository

**Rationale**: Easier to manage for small projects, coordinated deployments, shared documentation, and a single git history.

### JWT Authentication
**Decision**: Implement JWT-based authentication

**Rationale**: Stateless, works well with modern SPAs, no session storage, and simple to implement.

### RESTful API
**Decision**: Use REST instead of GraphQL

**Rationale**: Simpler to implement and understand, better HTTP caching, mature tooling, easier to test.

## Development Practices

### API-First Development
**Decision**: Define API contracts before implementation.

### Migrations as Code
**Decision**: Manage database schema with Alembic.

### Containerized Deployment
**Decision**: Deploy all services as containers.

---

## CCSA-specific decisions

These decisions extend or deviate from the defaults and directly answer questions from the challenge (scope, trade-offs, AI usage, risks).

### D1 — CSV input only (no PDF or Plaid for MVP)
**Decision**: The MVP accepts a CSV file uploaded by the user only.

**Alternatives considered**: Plaid (bank aggregator suggested by the brief), PDF parsing with OCR. The system should remain modular and extensible to accept other alternatives in a future implementation.

**Rationale**:
- Most banks allow exporting transactions to CSV → sufficient coverage without external dependencies.
- Plaid in production requires application, approval, and possible costs; the sandbox does not provide real user data.
- Bank PDFs vary too much in format to parse reliably within 72 hours.

**Consequence**: Plaid and PDF support are "Could Have" items (see `PROJECT_SCOPE.md`). Choosing CSV eliminates the project's largest technical risk.

### D2 — Two-layer analysis with graceful degradation
**Decision**: Layer 1 = rules-based detection (regex/keywords + recurrence). Layer 2 = optional LLM that enriches results with finer categorization and natural-language recommendations. If Layer 2 fails or is disabled, return Layer 1 results.

**Rationale**:
- Guarantees a deliverable MVP even if AI fails on demo day (rate limits, inconsistent prompts).
- Aligns with the strategy "solid base first, AI as layer 2".
- Provides demonstrable evidence in the deliverable of where AI helped and where it failed: the fallback is explicit.

### D3 — Provider-agnostic LLM via `.env`
**Decision**: The AI layer is behind a common interface (`LLMProvider`) with implementations for Ollama (local) and OpenAI, selectable via `LLM_PROVIDER`.

**Rationale**:
- Local development is free with Ollama; production/demo can use OpenAI without code changes.
- Avoids vendor lock-in and exposure to a single provider's costs/limits.
- Reuses a familiar pattern validated by the developer.

### D4 — Do not persist raw files; minimize sensitive data
**Decision**: Parse the CSV in memory and store only normalized transactions needed for analysis. Do not log transactions or statement content.

**Rationale**: As a FinTech-related project, security and privacy are explicit evaluation criteria. Minimizing stored data reduces the attack surface and compliance risk.

**Note (Red zone in `AI_RULES.md`)**: Any change that touches user isolation, authentication, or handling of financial data must be reviewed line by line.

### D5 — No automatic subscription cancellation
**Decision**: The "extra" feature (automatic cancellation) is out of scope. The product recommends and explains; the user executes cancellations.

**Rationale**: Automatic cancellations require merchant integrations, per-service OAuth, and legal/operational implications that are unrealistic to implement in 72 hours. This is documented as a "Won't Have" to answer the question confidently in the demo.

### D6 — Persist analysis history
**Decision**: Each analysis is saved and associated with the user's account and can be retrieved later.

**Rationale**: The brief asks for "results saved" and enabling month-to-month tracking adds value (foundation for the "Could Have" of temporal comparisons).
