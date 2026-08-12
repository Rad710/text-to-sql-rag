---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
depends_on: []          # task numbers that must finish first
decision: null          # decisions/NNNN that governs this task, if any
---

# 0033 — Group config + rate limiter into an `app/config/` package

## Goal
`app/config.py` (settings) and `app/ratelimit.py` (per-user rate limiter) were two loose cross-cutting
modules at the top of the package. Group them into a single `app/config/` sub-package so the app-wide
infrastructure has one home. First step of the larger repo reorganization (plan: tasks 0033–0035); pure
relocation, no behavior change.

## Context
Both modules are pure and import-time-cheap (no DB/network). `app.config` is imported by ~17 sites
(incl. `alembic/env.py`), `app.ratelimit` by 3. Grouping cross-cutting infra under one package is the
idiomatic FastAPI convention (the official full-stack template uses `app/core/`); owner chose the name
`config`. Design log → [`discussion.md`](discussion.md).

## Plan
1. `mkdir app/config` then `git mv app/config.py app/config/config.py` and
   `git mv app/ratelimit.py app/config/ratelimit.py`.
2. Add `app/config/__init__.py` re-exporting the public API (`Settings`, `get_settings`, `LlmMode`,
   `DeployMode`, `RateLimiter`, `RateLimitResult`) so `from app.config import …` keeps working unchanged.
3. Repoint the 3 `from app.ratelimit import` sites to `from app.config import` (`app/api.py`,
   `tests/test_ratelimit.py`, `tests/test_api.py`). `app.config` importers are untouched (re-export).

## Done when
- [x] `app/config/` holds `config.py`, `ratelimit.py`, `__init__.py`; moves via `git mv` (history kept).
- [x] No `app.ratelimit` references remain; `from app.config import …` resolves everywhere.
- [x] Gates green: `ruff check .`, `ruff format --check .`, `mypy app evaluation`, `uv run pytest`
      (128 passed).

---
Log → [`discussion.md`](discussion.md)
