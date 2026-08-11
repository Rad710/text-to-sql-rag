---
status: accepted
date: 2026-08-11
---

# 0010 — Per-user rate limiting + two deploy modes (demo / live)

## Context
The showcase will be hosted (task 0014). The owner wants two flavors ready: a **mock-only** demo (safe
to leave open — deterministic, no external LLM, no cost) and a **real-LLM** deploy (Ollama/vLLM, decision
0015) where each model call costs tokens/latency. `/chat` executes model-written work behind a JWT
(decision 0009), so it needs abuse/cost protection. Two questions had real options: *what to key the
limit on*, and *how to implement it*.

## Decision
We will rate-limit **`/chat` per authenticated user** (keyed by JWT subject), not per IP. `/chat` always
carries a user identity, so per-user is the fair, meaningful unit and the natural place for a per-account
cost ceiling. Two independent windows guard each user: a **per-minute rate** (anti-hammering) and an
optional **per-day cap** (the cost ceiling), the latter active only in live mode.

The limiter is a **small pure, in-memory, clock-injected** module (`app/ratelimit.py`) — no Redis, no new
dependency — consistent with the project's pure-core rule (CLAUDE.md). State is per-process and resets on
restart; acceptable for a single-instance demo deploy.

A **`DEPLOY_MODE=demo|live`** env sets the rate-limit *defaults* (demo: 60/min, no daily cap; live:
20/min + 100/day); `RATE_LIMIT_PER_MIN` / `RATE_LIMIT_PER_DAY` override explicitly. The compose wiring
for each mode lands in task 0014.

## Consequences
- Good: fair per-account limiting + a real per-user daily cost ceiling for the live deploy; zero new
  dependencies; the decision logic unit-tests without a clock, DB, or FastAPI.
- Good: one code path, two documented env presets — the demo and live deploys differ only by config.
- Bad / cost: in-memory state is per-process, so limits reset on restart and are not shared across
  multiple app instances (a distributed store like Redis would be needed to scale out).
- Bad / accepted: **auth endpoints are not rate-limited** (owner's call for scope). A scripted client can
  farm accounts to get fresh per-user quota, or brute-force logins. Documented as a known limitation; a
  per-IP limit on `/auth/register|login` is the follow-up if the deploy ever needs it.

## Alternatives considered
- **Per-IP limiting** — rejected as the primary key: `/chat` is authenticated, so per-user is fairer and
  is the only key that supports a per-account cost cap. Per-IP mainly helps *unauthenticated* endpoints.
- **slowapi (or fastapi-limiter + Redis)** — rejected: a pure ~70-line limiter needs no dependency/Redis,
  unit-tests trivially, and is enough for a single-instance demo. Revisit if we scale to many instances.
- **Sliding-window / token-bucket** — rejected for now: a fixed window is simpler and adequate; the only
  visible artifact is a burst allowed right after a window boundary, which is fine here.
