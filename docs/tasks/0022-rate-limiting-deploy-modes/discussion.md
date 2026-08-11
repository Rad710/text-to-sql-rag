# 0022 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Consulted the owner on the three real choices. Keying: the backlog said "per-IP", but the
  owner steered to **per-user** — correct, since `/chat` is authenticated so per-user is the fair unit and
  the only key that supports a per-account cost cap. I flagged that per-user-only leaves account-farming /
  login brute-force unguarded (no auth-endpoint limit); the owner accepted that as scope. Mechanism:
  **custom pure limiter** (no slowapi/Redis) — matches the pure-core rule and unit-tests without a clock.
  Cost control: **yes**, a per-user daily cap (20/min + 100/day), active only in live mode. Recorded as
  [decision 0010](../../decisions/0010-rate-limiting-deploy-modes.md).
- 2026-08-11: Deploy-mode representation — chose a `DEPLOY_MODE=demo|live` knob that sets rate-limit
  *defaults* (explicit `RATE_LIMIT_PER_MIN`/`_PER_DAY` still win) + README presets, rather than pulling a
  live compose override into this task. Keeps the 0022/0014 boundary clean (0014 owns the compose/hosting).
- 2026-08-11: Built the pure `RateLimiter` as two fixed windows (minute + day) with **check-then-count**
  semantics, so a blocked key isn't further penalised and `retry_after` is just the time left in the
  tripped window. `enforce_chat_rate_limit` depends on `get_current_user` (so it keys by `user.id`) and on
  an overridable `get_chat_limiter()` provider — the api test injects a tiny limiter to force a 429 without
  fighting the demo defaults.
- 2026-08-11: **Layering fix caught in browser QA.** First cut had the backend detail end with "Probá de
  nuevo en un momento." *and* the frontend append "Probá de nuevo en {Retry-After} s." → the message
  doubled the phrase and printed a raw `28302 s` for the daily cap. Fixed the layering: the backend detail
  now carries the **reason only**; the frontend owns the retry hint and formats it (seconds when ≤ 90 s,
  else "más tarde"). Mirrors decision 0006's "backend = data, frontend = presentation" split.
- 2026-08-11: Browser-verified (throwaway Postgres :55432 + MySQL + mock LLM). Per-minute 429 confirmed by
  curl (two requests in one window → 429, `Retry-After: 15`); note the per-minute limit resets on the wall
  clock, so two *manual* browser clicks ~1 min apart straddle a window boundary and both pass — expected,
  not a bug. Demonstrated the 429 in-browser via a `RATE_LIMIT_PER_DAY=1` run: 2nd `/chat` → clean
  "⚠️ Alcanzaste el límite diario de consultas. Probá de nuevo más tarde." Gates: backend pytest/ruff/mypy
  green (123 tests); frontend lint/build/test green (17 tests).
