---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
depends_on: [0014]      # task numbers that must finish first
decision: null          # decisions/NNNN that governs this task, if any
---

# 0031 — Move all Docker files into a `docker/` folder

## Goal
The repo root had six Docker-related files scattered across the root and `frontend/` (`Dockerfile`,
`docker-compose.yml`, `docker-compose.prod.yml`, `docker-entrypoint.sh`, `frontend/Dockerfile`,
`frontend/nginx.conf`), making the root hard to scan. Collect them all under a single `docker/` folder so
the root is tidy and everything Docker lives in one place. No change to what the stacks do.

## Context
Files originate in tasks [0001](../0001-project-scaffold/) (backend `Dockerfile` + base compose),
[0002](../0002-synthetic-mysql-db/) (MySQL service), and [0014](../0014-deploy-live/) (prod compose +
frontend image + nginx). Owner asked for everything in `docker/` (including the compose files and the
frontend image), accepting the `-f docker/…` command change. Design log → [`discussion.md`](discussion.md).

## Plan
1. `git mv` the six files into `docker/`: `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`,
   `docker-entrypoint.sh`, `frontend/Dockerfile` → `docker/frontend.Dockerfile`, `frontend/nginx.conf` →
   `docker/nginx.conf`.
2. Repoint build so both images use the **repo root** as the build context (the frontend image now needs
   both `frontend/` and `docker/nginx.conf`, whose only common ancestor is the root):
   - `docker/Dockerfile`: `COPY docker/docker-entrypoint.sh ./`.
   - `docker/frontend.Dockerfile`: root-relative copies (`COPY frontend/package.json …`, `COPY frontend/ .`,
     `COPY docker/nginx.conf …`).
   - Both compose files: `build: { context: .., dockerfile: docker/… }`; MySQL init volume `../db/init`.
3. Consolidate `.dockerignore`: the root file now governs both images (excludes `**/node_modules`,
   `frontend/dist`, …); delete the now-dead `frontend/.dockerignore`.
4. Pin `name: text-to-sql-rag` in both compose files so container/volume names stay stable (compose would
   otherwise derive the project name from the `docker/` folder → orphaned `docker_*` volumes).
5. Update the commands in `README.md`, `DEPLOY.md`, `CLAUDE.md`, `.env.example` to `-f docker/…` (run from
   the repo root so the root `.env` is read); add an optional `COMPOSE_FILE=docker/docker-compose.yml` to
   `.env.example` so a bare `docker compose up` still runs the dev stack. Historical task/decision docs are
   left as-is (they record the state at the time).

## Done when
- [x] All six files live under `docker/`; the repo root has no loose Docker files; moves via `git mv`.
- [x] `docker compose -f docker/docker-compose.yml … config` and the prod file both resolve (context =
      repo root, dockerfiles under `docker/`, `db/init` at root, project name `text-to-sql-rag`).
- [x] Both images **build**: `build app` (backend) and `build web` (frontend, root context +
      `docker/nginx.conf`) succeed.
- [x] `README.md` / `DEPLOY.md` / `CLAUDE.md` commands use `-f docker/…`; no stale root-path commands.
- [x] Backend gates untouched and green (no app code changed).

## Follow-up for the owner (outside my tool permissions)
- `.env.example` is blocked by a permission hook, so apply this one edit by hand: change the comment
  `# --- Production web (docker-compose.prod.yml only) ---` to `docker/docker-compose.prod.yml`, and
  (optional) add `COMPOSE_FILE=docker/docker-compose.yml` near the top so `docker compose up` works bare.

---
Log → [`discussion.md`](discussion.md)
