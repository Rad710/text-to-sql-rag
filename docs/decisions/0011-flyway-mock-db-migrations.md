---
status: accepted
date: 2026-08-12
supersedes: 0004
---

# 0011 — Provision the mock query DB with Flyway migrations (supersedes 0004)

## Context
[0004](0004-synthetic-db-via-init-sql.md) stood up the synthetic MySQL query DB from three files under
`db/init/` (`01_schema.sql`, `02_seed.sql`, `03_grant_readonly.sh`), applied by MySQL's
`/docker-entrypoint-initdb.d` hook on first boot and, separately, replayed by hand in CI. Two things
prompted a change:

- **The real schema lives in a separate prod project.** The app introspects the live DB at runtime
  (`app/rag/introspect.py` reads `information_schema`); nothing in `app/` depends on these files. So this
  DB is explicitly a **mock** for the local demo — reflected by renaming `db/` → `mock-db/`.
- **The init-SQL mechanism is not real migration tooling.** It only runs on *first* boot (a persisted
  volume never re-applies changes), the read-only grant needed a bespoke shell script, and CI had to
  duplicate the apply logic with `mysql < …` + `bash`. We want versioned, idempotent, tool-managed
  migrations — the same discipline the real project uses.

## Decision
Provision the mock DB with **Flyway** versioned migrations living in `mock-db/migration/`:

- `V1__schema.sql` (was `01_schema.sql`), `V2__seed.sql` (was `02_seed.sql`), and `V3__readonly_user.sql`
  — the read-only-user grant re-expressed as SQL, with the password injected via a Flyway placeholder
  (`${db_password}` ← `FLYWAY_PLACEHOLDERS_DB_PASSWORD`) so no credential is committed. This deletes the
  `03_grant_readonly.sh` shell script.
- In docker-compose (base + prod), a **one-shot `flyway/flyway` service** runs `migrate` once MySQL is
  healthy, then exits; the `app` service waits on it via `depends_on: condition:
  service_completed_successfully`. Flyway's schema-history table makes re-runs idempotent, so a restart
  with a persisted `mysqldata` volume is a no-op.
- CI runs the **same migrations** with `docker run --rm --network host flyway/flyway … migrate` against
  the MySQL service container, replacing the `mysql < …` + `bash` steps.

Unchanged from 0004: the data is synthetic/obviously-fake, business tables only (no audit/trigger/auth
tables), and we never point at the real DYR Transportes database.

## Consequences
- **Positive:** one provisioning mechanism shared by compose *and* CI; versioned/idempotent migrations
  that survive volume persistence; the credential stays out of the SQL; demonstrates real migration
  tooling; `mock-db/` names the folder honestly.
- **Negative:** adds a Flyway container to the stack and a one-shot dependency edge; a fresh dev DB now
  needs the `flyway` service to run (e.g. `docker compose … up -d mysql postgres flyway`) rather than
  MySQL self-applying on boot. Documented in the README dev flow and DEPLOY.md.
- The **app-store Postgres** keeps using **Alembic** ([0008](0008-app-datastore-postgres.md)) — Flyway
  here is only for the mock MySQL query DB. Two DBs, two migration tools, by design (different roles).
