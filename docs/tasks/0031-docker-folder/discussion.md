# 0031 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Why.** Owner: "too many files in the [root] folder … hard to keep track." Six Docker files
  were spread across the root and `frontend/`. Move them all under `docker/`. Pure relocation — the stacks
  must do exactly what they did before.

- 2026-08-12: **Two choices surfaced before building** (owner picked both):
  1. *Move the compose files too* (not just the Dockerfiles), accepting that `docker compose up` becomes
     `docker compose -f docker/docker-compose.yml up`. Mitigation: an optional `COMPOSE_FILE` in `.env`
     restores the bare command for the dev stack.
  2. *Move the frontend image + nginx.conf into `docker/`* as well (rather than leaving them colocated in
     `frontend/`).

- 2026-08-12: **Build-context consequence of choice 2.** With `nginx.conf` in `docker/` and the frontend
  source in `frontend/`, a single Dockerfile can't reach both unless the build context is their common
  ancestor — the repo root. So both images now build from `context: ..` with `dockerfile: docker/…`, and
  the frontend Dockerfile uses root-relative paths (`COPY frontend/ .`, `COPY docker/nginx.conf …`). The
  backend already only copied selective paths, so root context is a no-op for it beyond a slightly larger
  context send (mitigated by `.dockerignore`).

- 2026-08-12: **`.dockerignore` can't move.** Docker only reads `.dockerignore` from the build-context
  root. Since the context is now the repo root for both images, the root `.dockerignore` governs both;
  `frontend/.dockerignore` would never be read again, so its patterns were folded into the root file
  (`**/node_modules`, `frontend/dist`, `frontend/.vite`, `frontend/coverage`, …) and it was deleted.

- 2026-08-12: **Project name pinned.** Compose derives the project name from the compose file's parent
  directory when unset. Moving the files to `docker/` would have flipped it from `text-to-sql-rag` to
  `docker`, prefixing new `docker_pgdata`/`docker_mysqldata` volumes and orphaning the old ones. Added
  `name: text-to-sql-rag` to both files to keep container/volume names exactly as before.

- 2026-08-12: **Verification.** `docker compose -f docker/docker-compose.yml … config` and the prod file
  both resolve (context = repo root, dockerfiles under `docker/`, `db/init` at root, name
  `text-to-sql-rag`). Both images build green — `build app` (backend; proves `COPY docker/docker-entrypoint.sh`
  + chmod) and `build web` (frontend; proves the root-context `COPY docker/nginx.conf`). A full `up` was
  skipped to avoid port-clashing with the running dev stack; runtime behavior is unchanged since only file
  locations moved. Backend code untouched, so its gates stay green.

- 2026-08-12: **`.env.example` left to the owner.** The permission hook blocks reading/editing `.env.example`
  from tooling, so the one comment fix (`docker-compose.prod.yml` → `docker/docker-compose.prod.yml`) and the
  optional `COMPOSE_FILE` line are handed over as a manual edit (README/DEPLOY/CLAUDE were updated directly).
