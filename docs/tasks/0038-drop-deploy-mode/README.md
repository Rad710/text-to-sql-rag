---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-13     # YYYY-MM-DD, last touched
decision: 0012          # decisions/NNNN that governs this task, if any
depends_on: []          # task numbers that must finish first
---

# 0038 — Drop `DEPLOY_MODE`; set rate limits directly

## Goal
Remove the `DEPLOY_MODE=demo|live` env knob. Its only effect was picking rate-limit *defaults* (demo
60/min no cap; live 20/min + 100/day) plus a `/health` label — redundant and misleading next to
`LLM_MODE`, which carries the real mode signal. Rate limits are now set only via the two explicit env
vars that already existed as overrides.

## Context
Owner review: "it should have another name if that is the only thing it does, since we already have
`LLM_MODE` as mock or openai." Weighed rename (`RATE_LIMIT_PROFILE`) vs. remove; owner chose **remove**.
Governed by [decision 0012](../../decisions/0012-drop-deploy-mode.md), which supersedes the deploy-mode
half of [0010](../../decisions/0010-rate-limiting-deploy-modes.md) (per-user rate limiting itself is
unchanged). The frontend never read `deploy_mode` (only `llm_mode`/`model`), so no UI change.

## Plan
- `config.py`: drop the `DeployMode` type, the `deploy_mode` field, and the preset branching in
  `get_settings`; `RATE_LIMIT_PER_MIN`/`_PER_DAY` default to `60`/`0`.
- `api.py`: drop `deploy_mode` from the `/health` payload.
- `tests/test_config.py`: replace the two deploy-mode tests with default + env-read rate-limit tests.
- `docker/docker-compose.prod.yml`: replace the `DEPLOY_MODE` passthrough with
  `RATE_LIMIT_PER_MIN`/`_PER_DAY` so the live cost ceiling stays settable in a container.
- Docs: README "Deploy modes" → "Rate limits"; DEPLOY.md §1/§5; `.env.example` (owner applies — perm).
- Decisions: new **0012** (supersedes 0010); mark 0010 `superseded`; update the decisions index.

## Done when
- [x] `DEPLOY_MODE` appears nowhere in `backend/app`, tests, compose, README, or DEPLOY.md.
- [x] Rate limits configurable via `RATE_LIMIT_PER_MIN`/`_PER_DAY` (host **and** prod compose).
- [x] `/health` no longer returns `deploy_mode`.
- [x] Decision 0012 added; 0010 marked superseded (body immutable); index updated.
- [x] Gates green: `pytest`, `ruff check`, `ruff format --check`, `mypy app evaluation`.
