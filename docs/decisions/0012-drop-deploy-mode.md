---
status: accepted
supersedes: 0010
date: 2026-08-13
---

# 0012 — Drop `DEPLOY_MODE`; set rate limits directly

## Context
[Decision 0010](0010-rate-limiting-deploy-modes.md) introduced a `DEPLOY_MODE=demo|live` env that
selected rate-limit **defaults** (demo: 60/min, no daily cap; live: 20/min + 100/day). In practice that
is the *only* thing it did — plus a label on `/health`. It does not switch the LLM, the DB, or any infra;
`LLM_MODE=mock|openai` already carries the real "which mode am I in" signal. Having a second `*_MODE`
knob that just picks defaults for two vars you can set yourself reads as redundant and misleading (it
sounds like it changes the deployment target).

## Decision
Remove `DEPLOY_MODE` entirely. `/chat` rate limits are configured **only** by the two explicit env vars
that already existed as overrides:

- `RATE_LIMIT_PER_MIN` (default `60`)
- `RATE_LIMIT_PER_DAY` (default `0` = no daily cap)

A real deploy sets them explicitly (e.g. `20` / `100`) to bound per-account cost. The per-user, in-memory,
clock-injected limiter and everything else in 0010 are unchanged — this only removes the preset indirection
and the `/health` `deploy_mode` field. The prod compose now passes `RATE_LIMIT_PER_MIN`/`_PER_DAY` through
so the live cost ceiling is still settable in a container.

## Consequences
- Good: one fewer concept; the two knobs are the single, obvious source of truth; no "mode" that silently
  overrides them.
- Good: `LLM_MODE` is now the only `*_MODE`, so "what mode is this" is unambiguous.
- Cost: a live deploy must set the two rate-limit vars itself instead of getting them from `DEPLOY_MODE=live`
  — documented in the README "Rate limits" section and DEPLOY.md §5.
- The `/health` payload loses `deploy_mode`; the frontend never read it (only `llm_mode`/`model`), so no UI
  change.

## Alternatives considered
- **Rename to `RATE_LIMIT_PROFILE`** — keeps the preset but with an honest name. Rejected: still a second
  knob whose whole job is to pick defaults for two vars already in the env; removing it is simpler.
- **Keep `DEPLOY_MODE` as-is** — rejected: the name overpromises (implies an environment/infra switch) and
  duplicates `LLM_MODE`'s role.
