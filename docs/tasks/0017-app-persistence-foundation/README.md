---
status: done
updated: 2026-08-11
depends_on: [0001]
decision: [0008]
---

# 0017 — App persistence foundation (Postgres + SQLAlchemy + Alembic)

## Goal
The writable **application datastore** that auth (0018), history (0019), and feedback (0020) build on —
a dedicated **Postgres** service, an async **SQLAlchemy** engine/session, and the `users` /
`conversations` / `messages` / `feedback` schema, migrated with **Alembic**
([decision 0008](../../decisions/0008-app-datastore-postgres.md)). Kept entirely separate from the
read-only MySQL query DB.

## Context
The query DB is `SELECT`-only by design (decision 0003); app state needs writes and its own store. This
task adds only the **foundation** — the endpoints/UI for auth/history/feedback are their own tasks. The
pure core (`app/safety`, `app/rag`, `app/llm`) must not import the store, so the DB-free unit tests stay
fast.

## Plan
**Stage A — store foundation** (this commit): deps (`sqlalchemy[asyncio]`, `asyncpg`, `alembic`); config
(`APP_DATABASE_URL`); a Postgres service in docker-compose; `app/store/` with `models.py` (ORM: `User`,
`Conversation`, `Message`, `Feedback`) + `engine.py` (async engine / sessionmaker / session dependency);
pure metadata unit tests.
**Stage B — migrations + live verification** (next commit): Alembic (`alembic.ini` + env + initial
migration off the models' metadata); an integration test that round-trips against a live Postgres; a
Postgres service in the CI integration job; `.env`/README notes.

## Done when
- [x] Deps pinned; `APP_DATABASE_URL` in config; `postgres:17` in docker-compose (separate from MySQL,
      own volume + healthcheck).
- [x] `app/store/models.py` defines the four tables; `app/store/engine.py` gives a lazy async session; the
      pure core does not import the store.
- [x] Alembic initial migration (`675aaf3ef12a`) creates the schema; an integration test round-trips
      (insert → query) user + conversation + message + feedback against a live Postgres; the CI integration
      job runs a Postgres service + `alembic upgrade head` + the test.
- [x] `ruff`/`mypy` (strict) / `pytest` green (108 unit DB-free; the round-trip opt-in via `-m integration`,
      verified locally against a throwaway `postgres:17`). Committed.

---
Log → [`discussion.md`](discussion.md)
