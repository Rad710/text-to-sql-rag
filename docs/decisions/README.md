# Decision log

Immutable records of design decisions. **Never edit an accepted record to reverse it** — add a new
numbered record that supersedes it, and link both ways. Template: [`_template.md`](_template.md).

| # | Decision | Status | Date |
|---|----------|--------|------|
| [0001](0001-tech-stack.md) | Python/FastAPI + MySQL + ChromaDB + OpenAI-compatible client, mock-default | accepted | 2026-08-10 |
| [0002](0002-agentic-tool-loop.md) | Build the core as a hybrid-agentic tool-loop, not a fixed pipeline | accepted | 2026-08-10 |
| [0003](0003-sql-safety-defense-in-depth.md) | Enforce read-only SQL in depth: DB user + sqlglot + LIMIT + connection hardening | accepted | 2026-08-10 |
| [0004](0004-synthetic-db-via-init-sql.md) | Materialize a synthetic demo DB via MySQL init SQL (not Alembic), business tables only | superseded by [0011](0011-flyway-mock-db-migrations.md) | 2026-08-10 |
| [0005](0005-custom-fastapi-sse-react-frontend.md) | Custom FastAPI SSE API + Vite/React/TS frontend (assistant-ui), not a chat framework (amends 0001's UI) | accepted | 2026-08-10 |
| [0006](0006-structured-results-over-sse.md) | Stream structured query results over SSE; the frontend owns table presentation | accepted | 2026-08-11 |
| [0007](0007-layered-package-structure.md) | Group `app/` into layered sub-packages (safety / rag / llm) by concern | accepted | 2026-08-11 |
| [0008](0008-app-datastore-postgres.md) | A separate Postgres app datastore (SQLAlchemy + Alembic) for users/conversations/feedback | accepted | 2026-08-11 |
| [0009](0009-auth-jwt.md) | Authentication via JWT bearer tokens | superseded by [0013](0013-hardened-bearer-jwt.md) | 2026-08-11 |
| [0010](0010-rate-limiting-deploy-modes.md) | Per-user /chat rate limiting (pure in-memory limiter) + demo/live deploy modes | superseded by [0012](0012-drop-deploy-mode.md) | 2026-08-11 |
| [0011](0011-flyway-mock-db-migrations.md) | Provision the mock query DB with Flyway migrations (`mock-db/migration/`), superseding 0004's init-SQL | accepted | 2026-08-12 |
| [0012](0012-drop-deploy-mode.md) | Drop `DEPLOY_MODE`; set `/chat` rate limits directly via `RATE_LIMIT_PER_MIN`/`_PER_DAY` (supersedes 0010's preset) | accepted | 2026-08-13 |
| [0013](0013-hardened-bearer-jwt.md) | Hardened bearer JWT: short-lived access (in memory) + rotating/reuse-detected refresh + strict CSP (supersedes 0009) | accepted | 2026-08-13 |
