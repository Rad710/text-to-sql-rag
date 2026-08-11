---
status: in-progress
updated: 2026-08-11
depends_on: [0009, 0015]
decision: 0010
---

# 0022 — Rate limiting + deploy modes (demo / live)

## Goal
Protect the hosted showcase from abuse and cap real-LLM cost: rate-limit `/chat` **per authenticated
user** (a per-minute rate plus an optional per-day cap), and add a `DEPLOY_MODE=demo|live` config that
picks sane limit defaults for the two deploy flavors the owner described — a safe mock-only demo and a
real-LLM deploy with tighter limits. Governed by [decision 0010](../../decisions/0010-rate-limiting-deploy-modes.md).

## Context
`/chat` is authenticated (decision 0009) and, in live mode, each turn drives a real model (decision 0015),
so per-user limiting is the fair unit and the place for a cost ceiling. The limiter is kept **pure** and
in-memory (no Redis/new dependency), matching the project's pure-core rule. The actual per-mode compose
wiring + hosting is task 0014; this task ships the limiter, the config knobs, the 429 UX, and tests.

**Known limitation (owner's scope call):** auth endpoints are *not* rate-limited — see decision 0010.

## Plan
1. `app/ratelimit.py` — a pure `RateLimiter` (fixed-window, clock injected): per-minute rate + optional
   per-day cap (`0` disables), `check(key, now) -> RateLimitResult{ok, retry_after, scope}`. No FastAPI/DB.
2. `app/config.py` — `deploy_mode: demo|live` (`DEPLOY_MODE`) driving defaults (demo 60/min, no daily cap;
   live 20/min + 100/day), overridable by `RATE_LIMIT_PER_MIN` / `RATE_LIMIT_PER_DAY`.
3. `app/api.py` — a memoized `get_chat_limiter()` provider + an `enforce_chat_rate_limit` dependency
   (keyed by `user.id`) on `/chat`; a denial → `429` with `Retry-After` and a Spanish *reason* only.
4. `frontend/src/runtime.ts` — render a 429 as the backend reason + a client-formatted retry hint
   (seconds for the per-minute wait; "más tarde" for the long daily wait), not a raw status line.
5. Tests: `tests/test_ratelimit.py` (pure — windows, caps, roll-over, retry_after), `tests/test_api.py`
   (429 + Retry-After via an injected tiny limiter), `tests/test_config.py` (mode defaults + env override),
   `frontend/src/runtime.test.ts` (both 429 hint branches).
6. Docs: decision 0010, this folder, a README "Deploy modes" section (env presets).

## Done when
- [x] `/chat` is rate-limited per user; over the budget → `429` + `Retry-After`; demo vs live pick
      different defaults; explicit env knobs override.
- [x] Pure limiter + config + api + frontend covered by tests; `pytest`/`ruff`/`mypy` green (backend),
      `pnpm lint`/`build`/`test` green (frontend).
- [x] 429 renders a friendly Spanish message (no raw status, no duplicated hint). Browser-verified:
      per-user 429 (per-minute, via curl) and the daily-cap 429 in-browser.
- [x] README documents the two deploy modes + env vars.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
