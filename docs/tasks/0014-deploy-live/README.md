---
status: in-progress
updated: 2026-08-11
depends_on: [0010, 0018, 0022]
decision: null
---

# 0014 — Deploy live (clickable showcase)

## Goal
Make the app runnable as a real, clickable deployment: a production `docker-compose` that builds and runs
all four pieces — **nginx serving the built SPA + reverse-proxying the API**, the **FastAPI app** (mock
mode, migrations on boot), the **MySQL** query DB, and the **Postgres** app store — behind a single
origin. Ship the artifacts + a `DEPLOY.md` runbook and finalize the docs; the owner does the actual host
step (VM, DNS, TLS).

## Context
Decisions (owner, 2026-08-11): **single VM + docker-compose**; **nginx serves the SPA and proxies the
API** (two containers, same origin → no CORS); the **public URL runs mock-only** (`DEPLOY_MODE=demo`),
with the real-LLM (`live`) path documented (decisions 0010 / 0015). All SPA calls are already relative
(`/chat`, `/auth`, `/conversations`, `/feedback`, `/health`), and Alembic reads `APP_DATABASE_URL`
(`alembic/env.py`), so same-origin proxying and migrations-on-boot need no app changes.

**Boundary:** the assistant produces + locally verifies the artifacts; provisioning the VM/DNS/TLS and
publishing the URL is the owner's step (documented in `DEPLOY.md`).

## Plan
1. `frontend/Dockerfile` — multi-stage: `node:22-alpine` (pnpm build → `dist/`) → `nginx:alpine` with
   `frontend/nginx.conf`. SPA fallback (`try_files … /index.html`) + proxy `/chat|/auth|/conversations|
   /feedback|/health` → `app:8000`, with **SSE-safe** proxy settings (`proxy_buffering off`, HTTP/1.1).
2. `Dockerfile` (app) — also copy `alembic/` + `alembic.ini`; add an entrypoint that runs
   `alembic upgrade head` then `exec uvicorn` (migrations on boot). Keep mock default.
3. `docker-compose.prod.yml` — standalone production stack: `mysql` (init scripts) + `postgres` (volume)
   + `app` (internal only, `DEPLOY_MODE=demo`) + `web` (nginx, publishes `:80`). Secrets via env; no
   public app port.
4. `DEPLOY.md` — runbook: prerequisites, `.env` for prod, `docker compose -f docker-compose.prod.yml up
   -d --build`, first-run notes, TLS options (Caddy/Cloudflare in front), the `live`-mode switch, and a
   teardown/backup note.
5. Finalize `README.md` (a "Deploy" section + hosted-URL placeholder) and `docs/ai-workflow.md`.
6. Verify locally: build + `up` the prod stack, browse the app **through nginx** (register → ask →
   table/chart → feedback), confirm SSE streams through the proxy; 0 console errors.

## Done when
- [x] `docker compose -f docker-compose.prod.yml up --build` brings up all four services healthy; the app
      is reachable on one origin through nginx (SPA + proxied API), SSE streams, migrations ran on boot.
      (Verified locally: `-p dyr-prod`, `WEB_PORT=8080`; app logs show the Alembic upgrade then uvicorn.)
- [x] Browser-verified end-to-end through nginx (register → question → result table + bar chart → 👍
      feedback persisted to prod Postgres), 0 console errors.
- [x] `DEPLOY.md` runbook covers prod `.env` (template), bring-up, TLS, and the demo↔live switch; README
      has a Deploy section; `docs/ai-workflow.md` reviewed (already final).
- [x] Existing CI gates unaffected (deploy artifacts only; no app/test changes).
- [ ] Committed.

## Owner step (not an assistant deliverable)
Provision the VM, put TLS in front (Caddy/Cloudflare), `docker compose -f docker-compose.prod.yml up -d
--build`, and fill the hosted URL into the README "Deploy" section. See `DEPLOY.md`.

---
Log → [`discussion.md`](discussion.md)
