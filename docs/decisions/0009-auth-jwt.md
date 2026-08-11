---
status: accepted
date: 2026-08-11
---

# 0009 — Authentication via JWT bearer tokens

## Context
Task 0018 adds real authentication (users / login / sessions) in front of the SPA + FastAPI backend.
The two common models for an SPA + API are stateless **JWT bearer tokens** and server-side **session
cookies**. A choice is needed before building the auth layer and the protected `/chat`.

## Decision
We will use **JWT bearer tokens**. On login the API issues a signed JWT (short-lived access token); the
React SPA stores it and sends it as `Authorization: Bearer <token>` on `/chat` and other protected
routes. Passwords are hashed (bcrypt/argon2) in the Postgres `users` table (decision 0008). Token
signing secret comes from the environment, never hardcoded (consistent with decision 0004's credential
policy).

## Consequences
- Good: stateless verification (no server session store); simple to reason about and to scale; clean
  `Authorization` header contract the SPA controls explicitly.
- Bad / cost: browser token storage has XSS trade-offs (mitigate: short token lifetime, no `dangerously`
  HTML, keep the token out of `localStorage` where practical); logout/refresh must be handled in code
  (a refresh-token flow if we want long sessions). Revoked-before-expiry needs a denylist if required.

## Alternatives considered
- **httpOnly session cookies** — safer against XSS (JS can't read the token) and a common SPA choice,
  but adds server-side session state / CSRF handling; rejected in favour of the stateless JWT contract.
