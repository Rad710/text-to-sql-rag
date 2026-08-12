# 0035 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Why + research.** Owner: the root "looks messy." Researched current practice (PyPA, pytest
  good-practices, the official `fastapi/full-stack-fastapi-template`, `zhanymkanov/fastapi-best-practices`).
  Dominant monorepo pattern: a **`backend/`** dir sibling to `frontend/`, package stays `app/`, `tests/`
  a sibling of `app/`, the eval harness out of the runtime package. `src/` layout gives no real benefit here
  (`package = false`, never built as a wheel). Owner approved `backend/`.

- 2026-08-12: **Package internals unchanged.** `pyproject` keeps `pythonpath=["."]`, `testpaths=["tests"]`,
  coverage `["app","evaluation"]`, mypy `app evaluation`; `alembic.ini` keeps `%(here)s/alembic` +
  `prepend_sys_path=.`. All of these resolve correctly when the command's CWD is `backend/`. So the move is
  purely about *where commands run*, not their config.

- 2026-08-12: **Docker.** Build context was already the repo root (task 0031), so the only change is a
  `backend/` prefix on the backend Dockerfile's COPY sources; image internals (`/app/app`,
  `uvicorn app.api:app`, entrypoint `alembic upgrade head`) are identical. Renamed
  `docker/Dockerfile` → `docker/backend.Dockerfile` to pair with `frontend.Dockerfile`.

- 2026-08-12: **CI.** `quality` is all-Python → job-level `defaults.run.working-directory: backend`. But
  `integration`/`e2e` mix a **root-level** Flyway step (`$PWD/mock-db/migration`) with Python steps, so a
  job-level default won't do — added per-step `working-directory: backend` to the uv/alembic/uvicorn steps
  and left the Flyway + frontend steps at their existing dirs.

- 2026-08-12: **pre-commit wrinkle.** The git hook runs from the repo root and reads the root
  `.pre-commit-config.yaml`, but the `mypy` local hook used `uv run …` — which now has no project at the
  root. Fixed the entry to `uv run --directory backend mypy app evaluation` (uv changes into backend, so
  `app`/`evaluation` resolve). ruff hooks are unaffected (per-file config discovery walks up to
  `backend/pyproject.toml`). Documented driving pre-commit from the root via `uvx pre-commit` so it doesn't
  need a project at the root. Config stays at the root (that's where the installed git hook looks). Verified
  the mypy entry runs clean from the repo root.

- 2026-08-12: **`.gitignore` needs nothing** — `.venv/`, `.mypy_cache/`, `.chroma/`, `.coverage`, etc. are
  non-rooted patterns, so they already match under `backend/`. Removed the orphaned root `.venv` (untracked);
  `uv sync` from `backend/` creates `backend/.venv`.

- 2026-08-12: **Verified.** From `backend/`: `uv sync`, `ruff check .`, `ruff format --check`,
  `mypy app evaluation`, `uv run pytest` → 128 passed. `docker compose … config` resolves for base + prod;
  the **backend image builds** (`Image text-to-sql-rag-app Built`) with the repo-root context +
  `backend/`-prefixed COPY paths. CI YAML parses with the backend working-directories in place; the
  pre-commit mypy hook runs clean from the repo root. No behavior change.
