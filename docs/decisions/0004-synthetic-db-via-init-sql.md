---
status: accepted
date: 2026-08-10
---

# 0004 — Materialize a synthetic demo DB via MySQL init SQL (not Alembic), scoped to the business tables

## Context
The query target must be **self-contained and runnable by anyone** (`docker compose up`) — we cannot
"assume the schema exists" and point at the real DYR Transportes database: nobody else has it, and it
holds real family-business data that must never sit behind a public LLM query tool
([0001](0001-tech-stack.md) already fixed the demo DB as synthetic). The real schema is, however, already
defined in the `dyrtransportes_flask` SQLAlchemy models — so it should be **reused, not reinvented**.

Task 0002 originally proposed Alembic. But this demo DB is **static and read-only** — it never evolves at
runtime — so a migration *framework* (SQLAlchemy models + `env.py` + a version tree + a migrate step) is
overhead with no payoff.

## Decision
We will materialize the demo DB with plain **MySQL init scripts** run by the container on first boot
(`db/init/*` mounted into `/docker-entrypoint-initdb.d`, executed in filename order): `01_schema.sql` (DDL
lifted faithfully from the real models) · `02_seed.sql` (obviously-fake data, dates relative to `NOW()` so
"this month" always returns rows) · `03_grant_readonly.sh` (the `SELECT`-only `llm_readonly` user — the
real guarantee from [0003](0003-sql-safety-defense-in-depth.md)).

**Credentials come from the environment, never hardcoded.** Both passwords (`MYSQL_ROOT_PASSWORD`,
`DB_PASSWORD`) are supplied via a gitignored `.env` (template: `.env.example`); `docker compose` fails fast
if they are unset. The grant is a `.sh` (not `.sql`) precisely so it can read the password from the env —
no secret ever lands in a tracked file.

We include **only the 7 business tables** (`driver`, `route`, `product`, `shipment`, `shipment_payroll`,
`driver_payroll`, `shipment_expense`). The `*_audit` companion tables + triggers and the `user` auth table
are **omitted** — they are irrelevant to a read-only freight-query demo and would only add RAG noise.

## Consequences
- Good: self-contained and demoable by anyone; faithful to the real schema; simplest thing that works; the
  read-only user is provably enforced (tested). No migration-tool machinery to maintain.
- Bad / cost: no runtime schema-evolution story (fine — it's a fixed demo). If we ever want to show
  migrations, that's a separate, deliberate task.

## Alternatives considered
- **Alembic migrations** — the real project's tool; rejected here as over-engineering for a static
  read-only demo.
- **Assume the real DB exists / point at it** — rejected: not runnable by others and exposes real data.
- **Include audit tables + triggers** — rejected: noise the query assistant never needs.
