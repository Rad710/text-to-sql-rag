# 0033 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Why.** Part of the repo reorg (plan: tasks 0033–0035). Owner wanted `config.py` +
  `ratelimit.py` grouped into a folder. Research (official full-stack-fastapi-template) uses `app/core/`
  for cross-cutting infra (config/security); owner picked the literal name `config`, so the package is
  `app/config/` with `config.py` + `ratelimit.py` inside.

- 2026-08-12: **Re-export over rewrite-all-imports.** `app.config` had 17 importers. Rather than churn all
  of them to `app.config.config`, `app/config/__init__.py` re-exports the public API so every existing
  `from app.config import get_settings` keeps working. Only the 3 `app.ratelimit` sites had to change
  (that module name went away). Smallest diff, and the flat import path is the nicer public surface anyway.

- 2026-08-12: **git mv needed the dir first.** `git mv app/config.py app/config/config.py` failed until
  `app/config/` existed (`No such file or directory`); `mkdir app/config` then the two `git mv`s worked and
  git recorded them as renames.

- 2026-08-12: **Verified.** `ruff check .` (auto-merged the two now-duplicate `from app.config import`
  lines in `api.py`), `ruff format --check`, `mypy app evaluation` clean; `uv run pytest` → 128 passed,
  22 deselected. No behavior change.
