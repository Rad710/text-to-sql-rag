# 0038 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-13: **Origin.** While testing prod in both LLM modes, owner asked what `DEPLOY_MODE` does.
  Traced it: sets rate-limit defaults (`config.py`) + a `/health` label; nothing else (frontend has no
  `deploy_mode` reference). Owner: the name overpromises next to `LLM_MODE`.
- 2026-08-13: **Options.** (a) rename to `RATE_LIMIT_PROFILE` keeping the demo/live preset; (b) remove
  entirely, set `RATE_LIMIT_PER_MIN`/`_PER_DAY` directly; (c) rename var + values (relaxed/strict).
  Owner chose **(b) remove** — fewest concepts, the two knobs already existed as overrides.
- 2026-08-13: **Compose.** Removing the preset means a live deploy must set the two limits itself, so the
  prod compose now forwards `RATE_LIMIT_PER_MIN`/`_PER_DAY` to the app container (previously it only
  forwarded `DEPLOY_MODE`). Keeps the live per-account cost ceiling reachable in a container.
- 2026-08-13: **Decisions.** 0010 is immutable and its rate-limiting substance still stands, so it's
  marked `superseded` with a pointer and body kept intact; new **0012** records the removal and
  supersedes it (mirrors the 0004→0011 pattern).
- 2026-08-13: **Verified.** Gates green from `backend/`. `.env.example` DEPLOY_MODE line dropped by the
  owner (file is permission-blocked for the agent) — also fixes the stale `APP_DATABASE_URL`/`CHROMA_PATH`
  lines flagged during the same review.
