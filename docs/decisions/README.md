# Decision log

Immutable records of design decisions. **Never edit an accepted record to reverse it** — add a new
numbered record that supersedes it, and link both ways. Template: [`_template.md`](_template.md).

| # | Decision | Status | Date |
|---|----------|--------|------|
| [0001](0001-tech-stack.md) | Python/FastAPI + MySQL + ChromaDB + OpenAI-compatible client, mock-default | accepted | 2026-08-10 |
| [0002](0002-agentic-tool-loop.md) | Build the core as a hybrid-agentic tool-loop, not a fixed pipeline | accepted | 2026-08-10 |
| [0003](0003-sql-safety-defense-in-depth.md) | Enforce read-only SQL in depth: DB user + sqlglot + LIMIT + connection hardening | accepted | 2026-08-10 |
