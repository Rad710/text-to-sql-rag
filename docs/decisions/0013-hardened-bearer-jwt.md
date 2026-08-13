---
status: accepted
supersedes: 0009
date: 2026-08-13
---

# 0013 — Hardened bearer JWT: short-lived access + rotating refresh + strict CSP

## Context
[Decision 0009](0009-auth-jwt.md) authenticated the SPA with a single, long-lived JWT kept in
`localStorage` and sent as a `Bearer` header. For a portfolio/production repo that's the weak point:
`localStorage` is readable by any XSS, and a long-lived token means a stolen one is usable for its
whole lifetime. The owner wants to **keep bearer JWTs (not cookies)** but harden them.

Honest tradeoff, recorded up front: with no cookies, the **refresh token must live in `localStorage`**,
so it remains XSS-reachable. This model's security therefore comes from **(1) a short-lived access
token, (2) refresh-token rotation with reuse detection, and (3) a strict CSP** that makes XSS hard in
the first place — not from hiding a token. httpOnly cookies (rejected here by preference) would remove
the token from JS entirely; that's the only materially stronger option.

## Decision
- **Two token kinds**, distinguished by a `type` claim so one can't be used as the other:
  - **access** — ~15 min, `type: "access"`, sent as `Authorization: Bearer`, held **in memory only**
    (the `useSession` zustand store), never persisted.
  - **refresh** — ~14 days, `type: "refresh"`, carries a `jti`, persisted in `localStorage`.
- **Rotation + reuse detection** (server-side): each refresh token is one `refresh_tokens` row. `POST
  /auth/refresh` revokes the presented `jti` and issues a new pair; **replaying an already-revoked
  `jti` revokes the user's whole token family** and 401s. `POST /auth/logout` revokes.
- `get_current_user` requires an **access** token. `login`/`register` return both tokens.
- **Frontend**: a single `apiFetch` attaches the access token and, on a 401, refreshes once and retries
  — else signs out. No token plumbing in components; the three former module-level global-mutable
  singletons (auth `unauthorizedHandler`, `active-conversation`, feedback id) are replaced by the
  `useSession` store.
- **Strict, same-origin CSP** (`default-src 'self'`, `frame-ancestors 'none'`, no external origins) plus
  `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` in `docker/nginx.conf`.

## Consequences
- Good: a stolen access token expires in minutes; a stolen refresh token is single-use (rotation) and
  its reuse is detected and kills the family; CSP shrinks the XSS surface that the model relies on.
- Good: the frontend is *simpler* — no token juggling in components, one `apiFetch`, one store.
- Cost: a `refresh_tokens` table + migration + the refresh/rotate/revoke logic and its tests.
- Accepted residual risk: the refresh token is in `localStorage` (XSS-reachable). Documented above; the
  CSP + short access TTL + rotation are the compensating controls. httpOnly cookies remain the stronger
  alternative if the constraint is ever lifted.

## Alternatives considered
- **httpOnly cookies** — strictly safer (token unreadable by JS; `SameSite=Strict` handles CSRF for a
  same-origin app). Rejected by owner preference to keep a bearer-token API.
- **Keep 0009 as-is** — rejected: long-lived token in `localStorage` is the exact exposure to fix.
- **Per-user `token_version` instead of a `refresh_tokens` table** — lighter, but no per-session
  revocation or reuse detection. Rejected for portfolio-grade correctness.
