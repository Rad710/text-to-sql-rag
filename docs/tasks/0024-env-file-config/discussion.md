# 0024 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Owner wants a proper `.env`-driven config and the guides to stop using inline env on the
  command line. Found `.env.example` was stale (predates 0017/0018/0022/0014) — missing
  `APP_DATABASE_URL`, `JWT_SECRET`, `DEPLOY_MODE`, rate limits, `APP_DB_PASSWORD`, `WEB_PORT`. No code
  change needed: `config.py` already `load_dotenv()`s and both composes interpolate `${…}`.
- 2026-08-11: Rewrote `.env.example` — every config var + compose-only secrets, sectioned, with a header
  explaining the one subtlety: `DB_HOST`/`APP_DATABASE_URL` are host-run values; docker compose ignores
  them (its own service networking) and only reads the secrets + `DEPLOY_MODE`/`LLM_MODE`/`WEB_PORT`.
  Verified: `docker compose --env-file .env.example config` resolves for BOTH base and prod, and every
  `config.py` env var has a line. Checked that Compose v5.4 strips inline `# comments` from values (so the
  commented template is safe) — confirmed `MYSQL_ROOT_PASSWORD: change-me-root` (comment stripped).
- 2026-08-11: Rewrote the README (Quickstart → `cp .env.example .env` + a "Local development" block; the
  real-model and deploy-mode snippets are now `.env` edits) and DEPLOY.md §1 (copy the template instead of
  a duplicated inline block). Removed the `VAR=… uv run …` patterns from documented commands.
- 2026-08-11: Set up a working local `.env` (backed up the stale one to `.env.bak.*`): mock/demo, a
  generated 64-byte `JWT_SECRET`, dev passwords, and `APP_DATABASE_URL` on **:55432** (this machine's 5432
  is held by a personal Postgres) + `WEB_PORT=8080`. Verified end-to-end with **no inline env**:
  `get_settings()` reads all values; `alembic upgrade head`, `uvicorn`, register → 201, `/chat` → answer
  all work sourcing only from `.env`. Torn down after. (A stale `dyr-pg-dev` container briefly caused an
  auth failure — recreated fresh; not a config issue.)
