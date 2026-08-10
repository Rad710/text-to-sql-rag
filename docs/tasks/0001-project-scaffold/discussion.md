# 0001 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Task created alongside the docs scaffold. Scope kept to skeleton + quality gates only — no
  DB, retrieval, or LLM logic (those are 0002+). Decisions 0001–0003 already recorded, so the stack and
  safety posture are settled before any code lands. Open choice deferred to implementation: MySQL driver
  (`PyMySQL` pure-Python vs `mysqlclient` C-ext) — lean `PyMySQL` for zero build deps unless perf argues
  otherwise.
