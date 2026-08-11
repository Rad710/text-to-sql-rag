# 0013 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-11: Scheduled after the CI-warning cleanup. Two small nets a reviewer expects: local
  pre-commit + coverage in CI. Kept tooling-only (no behavior change).
- 2026-08-11: Choices —
  - **mypy as a `local` hook** (`uv run mypy app evaluation`), not `mirrors-mypy`: mypy needs the
    project's own deps to resolve imports, which the mirror's isolated venv doesn't have. `pass_filenames:
    false` so it type-checks the whole packages, matching CI.
  - **ruff-pre-commit pinned to v0.16.2** — the exact ruff already in the dev group, so local and CI can't
    disagree on lint/format. Hook ids `ruff-check` (+`--fix`) and `ruff-format`.
  - **Coverage floor `fail_under = 80`**, not a ratchet: measured unit coverage is ~87%, so 80 is a floor
    with headroom that catches a real regression without failing on small, legitimate shifts. The unit run
    (the quality job) excludes the DB-heavy modules (`rag/introspect`, `store/conversations`,
    `auth/service`) on purpose — those are exercised by the separate integration job, which doesn't collect
    coverage. Documented so the 87% isn't mistaken for total coverage.
  - Pre-commit left the Python hooks + basic hygiene; **frontend Biome stays in its own CI job** (not added
    as a hook) to keep this task's scope to the stated ruff/ruff-format/mypy.
- 2026-08-11: `pre-commit run --all-files` passed after auto-fixing two missing trailing newlines
  (`frontend/src/index.css`, `alembic/README`); re-run is clean/idempotent. `pytest --cov` reports
  **87.07%** ("Required test coverage of 80.0% reached"), 123 unit tests green.
