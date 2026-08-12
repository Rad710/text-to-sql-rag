---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
depends_on: []          # task numbers that must finish first
decision: 0011          # decisions/NNNN that governs this task, if any
---

# 0034 — Rename `db/` → `mock-db/` and provision it with Flyway

## Goal
The `db/init/*` scripts (schema + seed + a shell read-only-grant) only stood up a **local mock** of the
DYR Transportes DB — the real schema lives in a separate prod project and the app introspects it live at
runtime. Rename the folder to say so (`mock-db/`) and replace the first-boot init scripts with **Flyway**
versioned migrations, so provisioning is real migration tooling shared by docker-compose and CI. Behavior
(the resulting synthetic DB) is unchanged. Second step of the repo reorg (plan: 0033–0035).

## Context
The app never reads these files (`app/rag/introspect.py` reads `information_schema` at runtime) — they only
seed the demo DB via MySQL's init hook + a duplicated CI apply. Decision **0011** (supersedes 0004) records
the rationale. Design log → [`discussion.md`](discussion.md).

## Plan
1. `git mv db mock-db`; restructure to `mock-db/migration/`: `V1__schema.sql` (was `01_schema.sql`),
   `V2__seed.sql` (was `02_seed.sql`), and a new `V3__readonly_user.sql` (the grant as SQL, password via the
   `${db_password}` Flyway placeholder). Delete the `03_grant_readonly.sh` shell script.
2. docker-compose (base + prod): drop the `/docker-entrypoint-initdb.d` mount + the init-only `DB_USER`/
   `DB_PASSWORD` env on `mysql`; add a one-shot **`flyway/flyway:11`** service (`migrate`, `depends_on:
   mysql: service_healthy`, migrations mounted at `/flyway/sql`, `FLYWAY_PLACEHOLDERS_DB_PASSWORD`); make
   `app` wait on `flyway: service_completed_successfully`.
3. CI (`integration` + `e2e`): replace the `mysql < …` + `bash` apply with a
   `docker run --network host flyway/flyway:11 … migrate` against the MySQL service.
4. New ADR `0011-flyway-mock-db-migrations.md`; mark `0004` superseded (status line + index only — body
   immutable). Repoint live docs (README dev flow, DEPLOY.md, CLAUDE.md tech-stack) off `db/init`.

## Done when
- [x] `mock-db/migration/{V1__schema,V2__seed,V3__readonly_user}.sql`; `db/` and the shell grant gone.
- [x] Both compose files validate (`config`) with the `flyway` service + `service_completed_successfully`
      edge; CI YAML parses.
- [x] **Flyway smoke test**: against a throwaway MySQL, `migrate` applies V1–V3; all 7 business tables +
      seed present; `llm_readonly` has exactly `SELECT ON dyrtransportes.*` — can SELECT, `CREATE TABLE`
      denied (ERROR 1142). Read-only guarantee (decision 0003) holds.
- [x] No live references to `db/init` / `03_grant_readonly.sh` remain; decision 0011 recorded, 0004
      superseded.

---
Log → [`discussion.md`](discussion.md)
