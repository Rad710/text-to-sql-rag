# 0017 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: **Stage A — store foundation.** Added deps (`sqlalchemy[asyncio]` 2.0, `asyncpg`, `alembic`);
  a `postgres:17` service in docker-compose (separate from the read-only MySQL query DB, own volume +
  `pg_isready` healthcheck; app gets `APP_DATABASE_URL`); config `app_database_url` (async DSN, env
  `APP_DATABASE_URL`). New `app/store/` package: `models.py` (SQLAlchemy 2.0 declarative `User` →
  `Conversation` → `Message` + one-per-message `Feedback`, all cascading) and `engine.py` (lazy async
  engine / `async_sessionmaker` / `get_session` dependency — no connection on import). Pure metadata tests
  (`tests/test_store.py`) assert the four tables, key columns, the FK chain, and the feedback uniqueness —
  no DB needed. mypy strict clean on the ORM (SQLAlchemy 2.0 native typing); 108 tests green. The pure core
  (safety/rag/llm) does not import the store.
- 2026-08-11: **Stage B (next):** Alembic init + initial migration off `Base.metadata`; an integration test
  that round-trips against a live Postgres; a Postgres service in the CI integration job.
