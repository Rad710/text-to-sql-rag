---
status: done
updated: 2026-08-11
depends_on: [0017, 0010]
decision: [0009]
---

# 0018 — Authentication (JWT)

## Goal
Real auth in front of the app ([decision 0009](../../decisions/0009-auth-jwt.md)): register + login,
bcrypt-hashed passwords in the Postgres `users` table (0017), a signed **JWT** the SPA sends as
`Authorization: Bearer …`, a **protected `/chat`**, and a React login/register screen.

## Context
Builds on the app datastore (0017) and the frontend (0010). Keep auth in its own `app/auth/` package;
secrets (JWT signing key) come from the environment (decision 0004 policy). The mock LLM default and the
SQL-safety layers are unaffected.

## Plan
**Stage A — backend** (this commit): deps (`pyjwt`, `bcrypt`); config (`jwt_secret`, `jwt_algorithm`,
`jwt_expiry_min`); `app/auth/` — `security.py` (hash/verify + JWT create/decode), `service.py` (async
register/authenticate over the store), `router.py` (`POST /auth/register`, `POST /auth/login`,
`GET /auth/me`), `deps.py` (`get_current_user` from the Bearer token); protect `/chat` with it; unit tests
(hash + JWT + 401-without-token) + an integration test (register → login → `/auth/me`).
**Stage B — frontend** (next commit): a login/register screen, JWT storage, an `Authorization` header on
`/chat`, logout; gate the Thread behind auth; tests + browser verification.

## Done when
- [x] `POST /auth/register` + `POST /auth/login` issue a JWT; passwords bcrypt-hashed; `GET /auth/me`
      returns the current user; `/chat` is 401 without a valid token, 200 with.
- [x] Secrets from env; unit tests (hash round-trip, JWT round-trip, `/chat` 401) + an integration test
      (register → login → me) green; `ruff`/`mypy` (strict)/`pytest` green (112 unit).
- [x] Frontend login/register + Bearer header + logout; the chat is reachable only when authenticated;
      Biome + vitest green; **browser-verified** (register → authenticated query streams → logout → login).
- [x] Committed.

---
Log → [`discussion.md`](discussion.md)
