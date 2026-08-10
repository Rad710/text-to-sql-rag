---
status: proposed
updated: 2026-08-10
depends_on: []
decision: 0001
---

# 0001 — Project scaffold + tooling

## Goal
Stand up the empty project so every later task has a home: a runnable FastAPI app (returning a stub in
mock mode), the config module, and the full quality-gate toolchain (tests, lint, types, CI, containers).
After this, `uvicorn app.main:app` runs with **no API key**, and `pytest`/`ruff`/`mypy` all pass green.

## Context
Governed by [decision 0001](../../decisions/0001-tech-stack.md) (stack) and the module map in
[`../../architecture.md`](../../architecture.md). No app logic yet — just the skeleton and the gates that
keep later work honest. Pure/impure separation and mock-default are set up now so they're not retrofitted.

## Plan
1. `pyproject.toml` — project metadata, pinned deps (`fastapi`, `uvicorn`, `openai`, `sqlglot`,
   `chromadb`, `pymysql`/`mysqlclient`, `alembic`, `sqlalchemy`), dev deps (`pytest`, `ruff`, `mypy`),
   tool config (ruff, mypy, pytest).
2. `app/__init__.py`, `app/config.py` (frozen `Settings` dataclass, env-driven, `LLM_MODE=mock` default,
   no DB/network on import), `app/main.py` (FastAPI app + `/health` + a stub `/chat` that echoes in mock).
3. `tests/test_config.py` — settings load from env with mock default; import does no I/O.
4. `.env.example`, `.gitignore`, `.dockerignore`, `LICENSE` (MIT).
5. `Dockerfile` (python:3.12-slim) + `docker-compose.yml` (app service; MySQL added in 0002).
6. `.github/workflows/ci.yml` — matrix py3.11/3.12: `ruff check`, `ruff format --check`, `mypy app`,
   `pytest`.
7. `README.md` — quickstart (mock-mode run) + link to `docs/`.
8. Fill the "Build & dev commands" placeholder in [`../../CLAUDE.md`](../../CLAUDE.md).

## Done when
- [ ] `uvicorn app.main:app` starts with no env set; `GET /health` returns 200; `POST /chat` returns a
      mock stub.
- [ ] `pytest` passes; `ruff check .` and `ruff format --check .` clean; `mypy app` clean.
- [ ] Importing `app.config` performs no DB or network I/O (asserted by a test).
- [ ] `.github/workflows/ci.yml` runs the four gates and is green on the branch.
- [ ] `.env.example` documents every setting; no secrets committed.
- [ ] CLAUDE.md "Build & dev commands" reflects the real commands.

---
Log → [`discussion.md`](discussion.md)
