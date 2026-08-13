---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-13     # YYYY-MM-DD, last touched
decision: 0013          # decisions/NNNN that governs this task, if any
depends_on: []          # task numbers that must finish first
---

# 0039 — Harden bearer-JWT auth + replace the frontend global-state hacks

## Goal
Raise the frontend to production/portfolio grade. Two entangled fixes: (1) harden auth — short-lived
access token (in memory) + a rotated, reuse-detected refresh token + strict CSP, replacing the single
long-lived JWT in `localStorage`; (2) replace the three module-level global-mutable singletons with a
`zustand` session store and de-string-ify the runtime adapter.

## Context
Owner audit of the frontend: "the usage of the global vars like that seems bad practice … react has
hooks … many things done hacky." Confirmed offenders: `api/auth.ts` `unauthorizedHandler`,
`lib/active-conversation.ts`, `api/feedback.ts` id — all out-of-React globals feeding a module-level
runtime adapter — plus `runtime.ts` round-tripping usage through a brittle regex. Owner also rejected
the "acceptable for a demo" framing on the `localStorage` token and chose **hardened bearer JWT (not
cookies)**. Governed by [decision 0013](../../decisions/0013-hardened-bearer-jwt.md) (supersedes 0009).

## Plan
**Backend** — `security.py` (access/refresh tokens with a `type` claim + `jti`); `RefreshToken` model +
Alembic migration; `service.py` (`issue_tokens`/`rotate_tokens`/`revoke`/`revoke_all` with reuse
detection); `router.py` (`/auth/refresh`, `/auth/logout`, both tokens on login/register); `deps.py`
(require `type:"access"`); config (`JWT_ACCESS_EXPIRY_MIN`, `JWT_REFRESH_EXPIRY_DAYS`).
**Frontend** — `stores/session.ts` (zustand; access in memory, refresh persisted); `api/client.ts`
(`apiFetch` = attach token + refresh-once-on-401); rewrite `api/auth.ts`; delete `context/AuthProvider`
+ `lib/active-conversation`; `useAuth` → store selector; bootstrap in `App`; rewire runtime / ChatPane /
ChatPage / feedback / conversations; de-string-ify `runtime.ts` (answer + usage as separate parts).
**Infra** — strict CSP + security headers in `docker/nginx.conf`.
**Tests** — backend `test_auth` (rotation + reuse + logout + type-mismatch); frontend `auth.test`
(login/refresh/sign-out) + `App.test` (bootstrap-via-refresh).

## Done when
- [x] Access token never in `localStorage`; refresh token rotated + reuse-detected server-side.
- [x] The three global-mutable modules are gone; state lives in the `useSession` store.
- [x] `runtime.ts` has no usage-string regex (answer/usage are separate parts).
- [x] Strict CSP + security headers served by nginx.
- [x] Decision 0013 added; 0009 superseded (body immutable); indexes updated.
- [x] Gates green: backend `pytest`/`ruff`/`mypy`; frontend `biome`/`tsc`/`vitest` + production build.
