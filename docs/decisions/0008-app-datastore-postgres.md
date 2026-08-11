---
status: accepted
date: 2026-08-11
---

# 0008 — A separate Postgres app datastore for users, conversations, and feedback

## Context
Full auth, conversation history/persistence, and persisted feedback all need **writes**. The synthetic
query database is deliberately **read-only** (decision 0003) and its schema is a fixed, static business
model (decision 0004) — app state must not live there. We need a second, writable store for
application data, isolated from the query path.

## Decision
We will run a **dedicated Postgres service** (a separate docker-compose container) for application
state — `users`, `conversations`, `messages`, `feedback`. Access it with **SQLAlchemy** (async) and
manage its schema with **Alembic** migrations. (Alembic was rejected only for the *synthetic* query DB
in decision 0004 because that schema is static; the app schema genuinely evolves, so migrations fit.)
This keeps a hard boundary: the read-only MySQL query DB + its `SELECT`-only user are untouched; all
writes go to Postgres under a separate app user.

## Consequences
- Good: clean separation of concerns (query data vs app data); a real, production-shaped persistence
  layer (Postgres + SQLAlchemy + Alembic) — strong engineering signal; matches the reference app's stack.
- Bad / cost: a second database engine and container to run, migrate, and deploy; the zero-setup story
  now includes bringing up Postgres (compose handles it locally; a managed instance in deploy).

## Alternatives considered
- **SQLite (embedded)** — simplest, zero extra infra, but a second storage tech and a weaker production
  signal; rejected in favour of a real server.
- **Reuse the MySQL server (separate writable schema/user)** — no new engine, but mixes app state into
  the query DB's container and blurs the read-only boundary; rejected for a cleaner split.
