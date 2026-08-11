# 0014 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Consulted the owner on the three shaping decisions: **single VM + docker-compose** host;
  **nginx serves the SPA and reverse-proxies the API** (two containers, one origin → no CORS); the public
  URL runs **mock-only** (`DEPLOY_MODE=demo`), with the real-LLM (`live`) path documented. Clarified the
  boundary: the assistant produces + locally verifies the artifacts; the owner does the VM/DNS/TLS + the
  actual hosted URL.
- 2026-08-11: Built — `frontend/Dockerfile` (node build → nginx) + `frontend/nginx.conf` (SPA fallback +
  SSE-safe API proxy: `proxy_buffering off`, HTTP/1.1, `Connection ""`, 300s read timeout); root
  `Dockerfile` now copies `alembic/` + `alembic.ini` and uses `docker-entrypoint.sh` (idempotent
  `alembic upgrade head` then `exec uvicorn`); `docker-compose.prod.yml` (standalone: mysql + postgres +
  app internal-only + web publishing `${WEB_PORT:-80}`); `DEPLOY.md` runbook; README "Deploy" section.
  `.env.prod.example` couldn't be written (sandbox blocks `.env*`), so the env template lives in DEPLOY.md.
- 2026-08-11: **Two Docker build bugs found + fixed during local verification** (exactly the kind CI's
  build-only check wouldn't catch without actually running compose):
  1. `pnpm install` failed on pnpm's `minimumReleaseAge` policy — the Dockerfile didn't copy
     `frontend/pnpm-workspace.yaml` (which carries the release-age excludes **and**
     `onlyBuiltDependencies` for esbuild/oxide/biome native binaries) before install. Fixed by copying it
     with package.json + lockfile.
  2. `pnpm build` failed a deps-status check because `COPY . .` clobbered the image's node_modules with
     the host's 503 MB copy — no `frontend/.dockerignore`. Added one (node_modules, dist, …).
- 2026-08-11: Verified the full prod stack locally (`-p dyr-prod`, `WEB_PORT=8080`, secrets via env):
  all four services came up healthy (postgres → mysql → app healthy → web); app logs show
  `Running upgrade → 675aaf3ef12a` then uvicorn. Through nginx: `GET /health` ok, SPA served,
  register→login (Postgres write), asked "facturación total por ruta" → SSE streamed through the proxy →
  tool steps + result table + **bar chart** + 👍 feedback persisted (`rating=1` row in prod Postgres;
  counts: 1 user / 1 convo / 2 msgs / 1 fb). **0 console errors.** Torn down with `down -v`.
- 2026-08-11: `docs/ai-workflow.md` reviewed for "finalization" — already complete, no placeholders/TODOs;
  left unchanged rather than add filler. README gained the Deploy section + a hosted-URL placeholder the
  owner fills in once live.
