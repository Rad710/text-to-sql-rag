---
status: in-progress
updated: 2026-08-11
depends_on: [0001]
decision: null
---

# 0013 — Dev-experience polish: pre-commit + coverage

## Goal
Two low-cost quality nets a reviewer looks for: a **`.pre-commit-config.yaml`** so the same gates CI runs
(ruff lint, ruff-format, mypy) also run locally before each commit, and **coverage reporting** in CI so
the "how well tested is this" story is visible and a big regression fails the build. No behavior change —
tooling only.

## Context
CI already runs ruff / ruff-format / mypy / pytest (`.github/workflows/ci.yml`); pre-commit just moves
those left so drift is caught before a push (the auth-drift and Vite-proxy bugs this project hit would
have shown up locally). Unit coverage measured today is **86%** (`pytest -m "not integration"`); the
DB-heavy modules (`rag/introspect`, `store/conversations`, `auth/service`) are covered by the separate
**integration** job, not the unit run, so the quality-job number legitimately excludes them.

## Plan
1. `.pre-commit-config.yaml`:
   - `pre-commit/pre-commit-hooks` v6.0.0 — trailing-whitespace, end-of-file-fixer, check-yaml,
     check-toml, check-merge-conflict, check-added-large-files.
   - `astral-sh/ruff-pre-commit` v0.16.2 (pinned to our ruff) — `ruff-check --fix` + `ruff-format`.
   - a **local** `mypy` hook running `uv run mypy app evaluation` (needs the project env, so not the
     isolated mirror), `pass_filenames: false`.
2. `pyproject.toml`: add `pytest-cov` + `pre-commit` to the dev group; add `[tool.coverage.run]` /
   `[tool.coverage.report]` (`source = app, evaluation`, `show_missing`, `exclude_lines` for pragmas /
   `TYPE_CHECKING`, `fail_under = 80` — a floor with headroom under today's 86%, not a brittle ratchet).
3. `.github/workflows/ci.yml`: the quality job's pytest step reports coverage
   (`--cov=app --cov=evaluation --cov-report=term-missing`); `fail_under` enforces the floor.
4. README: a short "Pre-commit" line under Development.
5. Run `pre-commit run --all-files` once; commit any auto-fixes it makes.

## Done when
- [ ] `pre-commit run --all-files` passes (ruff, ruff-format, mypy, hygiene hooks) on a clean tree.
- [ ] `uv run pytest` prints a coverage summary and fails if total < 80%; passes today (~86%).
- [ ] CI quality job shows the coverage report; all gates still green (`ruff`/`mypy`/`pytest`).
- [ ] README documents `pre-commit install`.
- [ ] Committed.

---
Log → [`discussion.md`](discussion.md)
