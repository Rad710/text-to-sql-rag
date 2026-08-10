# 0001 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Task created alongside the docs scaffold. Scope kept to skeleton + quality gates only — no
  DB, retrieval, or LLM logic (those are 0002+). Decisions 0001–0003 already recorded, so the stack and
  safety posture are settled before any code lands. Open choice deferred to implementation: MySQL driver
  (`PyMySQL` pure-Python vs `mysqlclient` C-ext) — lean `PyMySQL` for zero build deps unless perf argues
  otherwise.
- 2026-08-10: Built. Kept core deps minimal (`fastapi`, `uvicorn`, `python-dotenv`); DB/RAG/LLM deps are
  deferred to the tasks that first need them (noted in `pyproject.toml`) to keep each commit's footprint
  honest and CI light. Config is a frozen `slots` dataclass with an `lru_cache`d `get_settings()`.
- 2026-08-10: **uv** chosen as the env/dependency tool (user-confirmed over pip/Poetry) — lockfile
  reproducibility (local == CI == Docker) and speed; same `uv sync` in the Dockerfile and CI.
- 2026-08-10: Pinned Python **3.12** via `.python-version` — `uv` first resolved 3.13 (allowed by
  `requires-python = ">=3.12"`); pinning makes local match CI (`setup-uv` @ 3.12) and the documented target.
  Dropped the CI 3.11 matrix leg accordingly (would be rejected by `requires-python`).
- 2026-08-10: Gates verified locally — ruff clean, `ruff format --check` clean, mypy clean, 8/8 pytest.
  Live uvicorn smoke test on port 8137 returned `/health` 200 and the `/chat` mock stub. Done.
