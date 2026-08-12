---
status: done            # proposed → in-progress → done   (also: blocked | deferred | superseded)
updated: 2026-08-12     # YYYY-MM-DD, last touched
depends_on: []          # task numbers that must finish first
decision: null          # decisions/NNNN that governs this task, if any
---

# 0036 — Accept `sql` as an alias for the `run_sql` `query` argument

## Goal
In live mode (local Ollama `llama3.1:8b`), roughly half of data questions returned confidently-wrong
answers ("no hay información…"). Root cause: the `run_sql` tool schema names its parameter `query`, but
smaller local models often emit the argument as `sql` instead. The agent read only `arguments["query"]`,
so a perfectly valid query arrived empty → the validator rejected it as `"empty SQL"` → the model
hallucinated an explanation. Accept either key so a well-formed query is never dropped.

## Context
Surfaced during live-mode testing after the reorg (0033–0035). It is a model-compliance issue, not a
safety hole: the sqlglot validator + read-only DB user still enforce read-only whichever key is used.
Cloud/larger models follow the schema (`query`), which is why mock mode was always fine.

## Plan
- `backend/app/agent.py`: add `_sql_arg(arguments)` returning `arguments["query"] or arguments["sql"] or
  ""`; use it at both extraction points (the SSE `sql` trace and `_run_tool`'s `run_sql` branch).
- `frontend/src/lib/runtime.ts`: extend the `argsText` fallback to `args.query ?? args.sql ?? …` so the
  step renders bare SQL (not raw `{"sql":…}` JSON) when the model used `sql`.
- Test: `backend/tests/test_agent.py::test_run_sql_accepts_sql_arg_alias` — a `sql`-named call reaches the
  tool with the SQL intact and is captured in `result.sql`.

## Done when
- [x] Backend accepts `query` or `sql`; new unit test passes; full backend suite green (129) + ruff/mypy.
- [x] Frontend renders bare SQL for either arg name; lint + build + vitest (22) green.
- [x] Live re-test (llama3.1:8b) — the exact driver-aggregation query that failed twice now returns the
      correct table + answer; several other DB questions (route billing, count, JOIN for unpaid
      settlements) and general chit-chat ("hello how are you", capabilities) all behave correctly, 0
      console errors.

---
Log → [`discussion.md`](discussion.md)
