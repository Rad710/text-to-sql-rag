# 0002 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: User asked whether we even need to create the schema ("assume it exists"). Resolved as
  [decision 0004](../../decisions/0004-synthetic-db-via-init-sql.md): a public showcase must be self-
  contained and must not point at the real DB (real data) — so we materialize a *synthetic* copy, but
  reuse the real schema design and use lightweight init SQL instead of Alembic. Scoped to the 7 business
  tables (audit tables + triggers + `user` dropped as query-irrelevant noise).
- 2026-08-10: DDL taken from the real `dyrtransportes_flask` models (ground truth), not the reference.md
  summary — captured exact nullability, `DECIMAL` precisions (amounts 20,0; weights 10,0; money 10,2), the
  `server_default "0"` booleans, and the 6-column `unique_driver_ticket_date`.
- 2026-08-10: Integration tests made **opt-in** via a `pytest` `integration` marker (default `addopts`
  excludes them), so the fast unit lane stays DB-free; a dedicated CI `integration` job stands up MySQL,
  applies `db/init/*.sql`, and runs them — proving the read-only guarantee in CI.
- 2026-08-10: Verified locally with `docker compose up -d --wait mysql`. Guarded against a false-positive
  "healthy" (mysqladmin ping can pass mid-init) by asserting row counts + user existence via `docker exec`
  before running the suite. All 6 integration tests pass; write attempts as `llm_readonly` fail with 1142.
  Torn down with `down -v`. Done.
- 2026-08-10: **Reworked credential handling** (user feedback: no hardcoded passwords in a showcase).
  Moved both passwords to env vars — `docker-compose.yml` uses `${MYSQL_ROOT_PASSWORD:?}` / `${DB_PASSWORD:?}`
  (fail-fast, no literals); the grant became `03_grant_readonly.sh` reading `DB_PASSWORD` from the env
  (a `.sql` file can't interpolate env), portable via `MYSQL_HOST` for the CI TCP path; `.env.example`
  documents the required secrets; CI uses throwaway CI-only creds for its ephemeral service. Non-secret
  config (host/port/user/db-name) stays literal. Re-verified end-to-end.
