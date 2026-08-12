---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
depends_on: [0033, 0034]  # task numbers that must finish first
decision: null          # decisions/NNNN that governs this task, if any
---

# 0035 — Consolidate the Python backend under `backend/` (mirror `frontend/`)

## Goal
The Python backend was a flat top-level layout (`app/`, `tests/`, `evaluation/`, `alembic/` + `alembic.ini`,
`pyproject.toml`, `uv.lock`, `.python-version` all at the repo root), which made the root cluttered next to
`frontend/`, `docker/`, `mock-db/`, `docs/`. Move all of it under a single **`backend/`** directory — the
idiomatic monorepo layout (the official `fastapi/full-stack-fastapi-template` does exactly this) — so the
root is tidy and symmetric with `frontend/`. Also rename `docker/Dockerfile` → `docker/backend.Dockerfile`
to pair with `frontend.Dockerfile`. Final step of the repo reorg (plan: 0033–0035); no behavior change.

## Context
The package stays named `app/`; `pyproject` internals (`pythonpath=["."]`, `testpaths=["tests"]`,
coverage/mypy targets) all resolve unchanged when commands run with `backend/` as the working directory.
Only paths and invocation directories change. Design log → [`discussion.md`](discussion.md).

## Plan
1. `git mv` into `backend/`: `app/`, `tests/`, `evaluation/`, `alembic/`, `alembic.ini`, `pyproject.toml`,
   `uv.lock`, `.python-version`. `git mv docker/Dockerfile docker/backend.Dockerfile`.
2. `docker/backend.Dockerfile`: build context stays repo root, so COPY sources gain a `backend/` prefix
   (`COPY backend/pyproject.toml ./`, `COPY backend/app ./app`, `COPY backend/alembic …`, `COPY backend/alembic.ini …`;
   `COPY docker/docker-entrypoint.sh ./` unchanged). Point both compose files' `app.build.dockerfile` at it.
3. `.github/workflows/ci.yml`: `quality` gets `defaults.run.working-directory: backend`; the Python steps
   of `integration`/`e2e` get `working-directory: backend` (the root-level Flyway step and frontend steps
   stay put).
4. `.dockerignore`: switch to `**/`-globs (venv/caches now under `backend/`); ignore `backend/tests` +
   `backend/evaluation` (neither image copies them).
5. Docs/tooling: README + CLAUDE run backend commands from `backend/`; `.pre-commit-config.yaml` mypy hook
   runs `uv run --directory backend mypy app evaluation`, and pre-commit is driven from the repo root via
   `uvx pre-commit` (config stays at the repo root where the git hook reads it). `.gitignore` unchanged
   (its patterns are non-rooted, so they already match under `backend/`).

## Done when
- [x] Root holds only `backend/ frontend/ docker/ mock-db/ docs/ .github/` + top-level md/dotfiles; all
      Python moved via `git mv` (history preserved); `docker/backend.Dockerfile` renamed.
- [x] From `backend/`: `uv sync`, `ruff check .`, `ruff format --check .`, `mypy app evaluation`,
      `uv run pytest` all green (128 passed).
- [x] `docker compose … config` resolves (base + prod); the **backend image builds** with the repo-root
      context + `backend/` COPY paths.
- [x] CI YAML parses with the `backend` working-directories on the Python steps; the pre-commit mypy hook
      (`uv run --directory backend …`) runs clean from the repo root.
- [x] App behavior unchanged; the whole reorg (0033–0035) is pure relocation + a provisioning-tool swap.

---
Log → [`discussion.md`](discussion.md)
