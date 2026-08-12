# 0034 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Why.** Owner: the `db/` folder is "weird — why do we need it?" The real schema lives in a
  separate prod project; here it's only a **mock** for the demo. Confirmed by code: `app/rag/introspect.py`
  reads `information_schema` at runtime and nothing in `app/` touches `db/init`. So: rename `db/` →
  `mock-db/`, and (owner's ask) use **Flyway** for migrations instead of the "random script".

- 2026-08-12: **Supersede, don't rewrite, 0004.** The init-SQL decision is immutable; wrote a new ADR
  **0011** and set 0004's status to `superseded` (status line + index row only — body untouched). What
  survives from 0004: synthetic data, business tables only, never point at the real DB. What changes: the
  *mechanism* (init-SQL → Flyway).

- 2026-08-12: **The read-only grant as a migration.** `03_grant_readonly.sh` became `V3__readonly_user.sql`
  using a Flyway placeholder for the password: `IDENTIFIED BY '${db_password}'` ←
  `FLYWAY_PLACEHOLDERS_DB_PASSWORD`. Keeps the credential out of the committed SQL (same property the shell
  script had via env). Username `llm_readonly` + DB `dyrtransportes` are demo constants, so hardcoded (the
  schema files already hardcode `USE dyrtransportes`).

- 2026-08-12: **One-shot service, not an init hook.** Flyway runs as a short-lived compose service
  (`command: migrate`) gated on `mysql: service_healthy`; `app` waits on
  `flyway: service_completed_successfully`. Advantage over the old init hook: idempotent + versioned, so it
  survives the persisted `mysqldata` volume (the init hook only ever ran on first boot). Dropped the
  now-unused `DB_USER`/`DB_PASSWORD` env from the `mysql` service (they existed only for the init script).

- 2026-08-12: **Dev-flow gotcha.** `docker compose up -d mysql postgres` no longer auto-seeds the mock
  (Flyway is a separate service). Updated the README dev command to
  `up -d mysql postgres flyway`. CI likewise now runs Flyway (`docker run --network host flyway/flyway:11 …
  migrate`) instead of `mysql < …` — one provisioning path for compose and CI.

- 2026-08-12: **Verified end-to-end** (Flyway is new, so smoke-tested for real). Against a throwaway
  `mysql:8.4` on :13306, the exact CI invocation applied V1→V3; `SHOW TABLES` = the 7 business tables (+
  `flyway_schema_history`); `driver` seeded (4 rows); `SHOW GRANTS FOR 'llm_readonly'` = `USAGE` +
  `SELECT ON dyrtransportes.*`; as that user, `SELECT` returns 4 but `CREATE TABLE` → `ERROR 1142` (denied).
  Both compose files `config`-resolve with the flyway service; CI YAML parses. Python untouched → 0033's
  backend gates still hold. Container cleaned up.
