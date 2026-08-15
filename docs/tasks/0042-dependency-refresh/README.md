---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-15     # YYYY-MM-DD, last touched
depends_on: []
decision: null
---

# 0042 — Refresh every declared dependency version to the current latest

## Goal
Bring the project's declared dependency versions back in line with what's actually published. The
lockfiles had drifted much less than the specs: `backend/pyproject.toml` still declared floors from the
scaffold era (`sqlglot>=25`, `chromadb>=0.5`, `openai>=1.40`, `mypy>=1.11`, `pytest>=8.3`) while
`uv.lock` was already resolving major versions above them, so the specs no longer described what the
project runs or supports. This task re-pins the floors to today's latest, upgrades both lockfiles, and
bumps the pinned CI actions and pre-commit hook revs — with every quality gate re-run as proof.

## Context
Two lockfiles and two pin sites, all independent:

- `backend/pyproject.toml` + `backend/uv.lock` — runtime, extras (`embeddings`, `mcp`) and the `dev` group.
- `frontend/package.json` + `frontend/pnpm-lock.yaml`.
- `.pre-commit-config.yaml` — hook revs; the comment there requires `ruff-pre-commit` to track the same
  ruff as the `dev` group.
- `.github/workflows/` — `ci.yml` was already current; `release.yml` (task 0032) had never been bumped
  since it was written and was a full major behind on all five of its actions.

CLAUDE.md requires pinned dependency versions; the existing style is a `>=major.minor` floor per package,
kept, not converted to `==`. The `openai` bump crosses a major (2.x → 3.x) — the only SDK surface this
project uses is `OpenAI(base_url=…, api_key=…)` and `chat.completions.create(...)` in
`backend/app/llm/client.py`, both unchanged in 3.x.

Base-image majors (`python:3.12-slim`, `node:22-alpine`, `mysql:8.4`, `postgres:17`, `flyway:11`) are
**deliberately out of scope** — see `discussion.md`.

## Plan
1. Query PyPI and the npm registry for the current latest of every declared package.
2. Raise the floors in `backend/pyproject.toml` (runtime, both extras, `dev` group).
3. `uv lock --upgrade` + `uv sync`; re-run all four backend gates.
4. `pnpm update --latest` in `frontend/`; realign the declared ranges; re-run tsc/biome/vitest + build.
5. Bump `ruff-pre-commit` to match the new ruff, and the five action pins in `release.yml`.
6. Record the held base-image majors in `discussion.md`.

## Done when
- [x] Every package declared in `backend/pyproject.toml` has a floor at its current latest minor
      (`sqlglot>=30.17`, `chromadb>=1.5`, `openai>=3.1`, `fastapi>=0.141`, `bcrypt>=5.0`, `pytest>=9.1`,
      `mypy>=2.3`, `ruff>=0.16`, …).
- [x] `uv.lock` regenerated with `--upgrade` (openai 2.53→3.1, sqlglot 30.16→30.17, sqlalchemy
      2.0.51→2.0.52, uvicorn 0.52.1→0.52.3, ruff 0.16.2→0.16.3 + transitives).
- [x] All four backend gates green on the upgraded env: `pytest` 136 passed / 22 deselected,
      `ruff check`, `ruff format --check` (60 files), `mypy app evaluation` (34 files).
- [x] `frontend/package.json` + `pnpm-lock.yaml` at latest (@assistant-ui/react 0.15.12→0.15.14,
      shadcn 4.16.2→4.18.0, zustand 5.0.14→5.0.15, @testing-library/user-event 14.6.3→14.6.4); stale
      declared ranges (`react`/`react-dom` `^19.0.0`, `@types/react*` `^19.0.0`) realigned to installed.
- [x] Frontend gates green: `tsc --noEmit`, `biome check` (58 files), `vitest run` 25 passed, and a
      clean production build.
- [x] `.pre-commit-config.yaml` `ruff-pre-commit` bumped to `v0.16.3`, matching the `dev` group ruff.
- [x] `release.yml` actions bumped (checkout v4→v7, setup-buildx v3→v4, login v3→v4, metadata v5→v6,
      build-push v6→v7); `ci.yml` verified already current.
- [x] No source changes were needed — the bumps are spec/lock only.

---
Log → [`discussion.md`](discussion.md)
