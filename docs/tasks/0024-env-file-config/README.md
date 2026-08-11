---
status: in-progress
updated: 2026-08-11
depends_on: [0014, 0022]
decision: null
---

# 0024 — Single `.env` as the source of truth (docs stop using inline env)

## Goal
Make configuration a proper, complete **`.env`** file that both the app (`python-dotenv`) and docker
compose read — and rewrite the guides so every documented command relies on `.env` instead of prefixing
inline `VAR=… uv run …`. One copy-and-edit step, no ad-hoc env on the command line.

## Context
`.env.example` was stale — it predated the app store (0017), auth (0018), rate limiting/deploy modes
(0022), and the prod web port (0014), so a fresh `cp .env.example .env` was missing `APP_DATABASE_URL`,
`JWT_SECRET`, `DEPLOY_MODE`, the rate-limit knobs, `APP_DB_PASSWORD`, `WEB_PORT`, etc. Meanwhile the
README/DEPLOY guides taught inline env (`LLM_MODE=openai … uv run …`, `DEPLOY_MODE=live … JWT_SECRET=… uv
run …`), which the owner wants replaced by editing `.env`. `app/config.py` already calls
`load_dotenv()`, and both compose files interpolate `${…}` from `.env`, so no code change is needed.

Note: `.env` values `DB_HOST` / `APP_DATABASE_URL` are **host-run** values; docker compose uses its own
internal service networking for those and only pulls the secrets + `DEPLOY_MODE`/`LLM_MODE`/`WEB_PORT`.

## Plan
1. Rewrite `.env.example` — every `app/config.py` var + the compose-only secrets (`MYSQL_ROOT_PASSWORD`,
   `APP_DB_PASSWORD`, `WEB_PORT`), sectioned and commented, with safe defaults / `change-me` secrets.
2. `README.md` — Quickstart leads with `cp .env.example .env`; add a "Local development" block (DBs in
   Docker + `uvicorn`/`vite` reading `.env`); rewrite the real-model + deploy-modes snippets as `.env`
   edits, not inline env.
3. `DEPLOY.md` — replace the inline dotenv template with `cp .env.example .env` + which values to set.
4. Verify `.env.example` resolves both compose files and covers every config var; verify a generated
   `.env` drives the full host-run flow (alembic + API + register + /chat) with **no** inline env.

## Done when
- [x] `.env.example` is complete — both compose files resolve with it; every `config.py` var is present.
- [x] README + DEPLOY use `.env` (no inline `VAR=… uv run …` in documented commands).
- [x] End-to-end verified from `.env` alone: `alembic upgrade head`, `uvicorn`, register (201), `/chat`
      (answer) — all with no inline env. Host-run reads `.env`; compose interpolates it.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
