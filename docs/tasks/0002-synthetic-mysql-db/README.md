---
status: done
updated: 2026-08-10
depends_on: [0001]
decision: 0004
---

# 0002 — Synthetic DYR Transportes MySQL database

## Goal
Give the assistant something real to query: a **self-contained, synthetic** MySQL database with the DYR
Transportes freight schema and obviously-fake data, plus a `SELECT`-only user. After this, `docker compose
up` brings up MySQL, auto-applies the schema + seed + grant, and the read-only user can read everything but
write nothing.

## Context
Governed by [decision 0004](../../decisions/0004-synthetic-db-via-init-sql.md) (init SQL, not Alembic;
business tables only) and [0003](../../decisions/0003-sql-safety-defense-in-depth.md) (the read-only user is
the true safety guarantee). Schema shape: [`../../reference.md`](../../reference.md); DDL is lifted
faithfully from the real `dyrtransportes_flask` SQLAlchemy models to avoid drift.

## Plan
1. `db/init/01_schema.sql` — the 7 business tables (InnoDB, utf8mb4) with exact types/keys/FKs + the
   `unique_driver_ticket_date` constraint on `shipment`.
2. `db/init/02_seed.sql` — obviously-fake rows; `shipment`/expense dates relative to `NOW()` so
   this-month / last-month / this-year questions always return data; covers the canonical demo questions.
3. `db/init/03_grant_readonly.sh` — `llm_readonly` user with `GRANT SELECT` on `dyrtransportes.*` only;
   password read from the environment (`DB_PASSWORD`), never hardcoded.
4. `docker-compose.yml` — add a `mysql:8.4` service mounting `./db/init`; wire the `app` service's `DB_*`
   env to connect as `llm_readonly`; `app` waits on MySQL healthcheck.
5. `pyproject.toml` — add `pymysql`; register a `pytest` `integration` marker; default run excludes it.
6. `tests/test_db_integration.py` — `@pytest.mark.integration`: tables exist, seed rows present, and the
   read-only user's `INSERT` is rejected. Skips cleanly when no MySQL is reachable.
7. `.github/workflows/ci.yml` — add an `integration` job that stands up MySQL, applies the init SQL, and
   runs the integration tests (proves the read-only guarantee in CI).

## Done when
- [x] `docker compose up` starts MySQL and auto-applies schema + seed + grant with no manual steps.
      *(Verified: first boot applied all 3 scripts → 7 tables, 16 shipments, `llm_readonly` created.)*
- [x] All 7 tables exist; seed data present; the canonical demo questions have rows to return.
      *(Revenue-per-route query returns 4 routes / 16 trips.)*
- [x] `llm_readonly` can `SELECT` but `INSERT`/`UPDATE`/`DELETE`/DDL are rejected — 6 integration tests
      pass (4 parametrized write-rejection cases).
- [x] Unit gates stay green and fast (8 passed, 6 integration deselected by default).
- [x] Integration job added to CI. **No credentials in any tracked file** — passwords come from a
      gitignored `.env` (`.env.example` template); `docker compose` fails fast if unset.

---
Log → [`discussion.md`](discussion.md)
