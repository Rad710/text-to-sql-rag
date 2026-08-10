---
status: done
updated: 2026-08-10
depends_on: [0004, 0006, 0007]
decision: 0002
---

# 0008 — Agentic tool-loop (+ execution + self-correction)

## Goal
Compose everything into the actual product: a bounded loop where the model calls `search_schema` and
`run_sql`, gets results back, and iterates until it answers — with **execution-guided self-correction**
(errors and empty results fed back for a repair pass). This is the realization of
[decision 0002](../../decisions/0002-agentic-tool-loop.md).

## Context
Wires the RAG store ([0006](../0006-retrieval-engine/)), the LLM client ([0007](../0007-llm-client/)), and
the SQL-safety layer ([0004](../0004-sql-safety-layer/)). The connection hardening (layer 4 of
[decision 0003](../../decisions/0003-sql-safety-defense-in-depth.md)) lands here, with the live connection.

## Plan
1. `app/execution.py` — `run_sql(query, settings) -> RunResult`: validate → enforce LIMIT → execute as the
   read-only user on a fresh connection with `max_execution_time` + a row cap; returns a structured result
   (never raises) so errors can be fed back. `format_result()` renders it for a tool message.
2. `app/agent.py` — `answer_question(question, llm, tools, max_iterations)`: the loop (LLM → dispatch
   tool calls → feed results back → repeat), tools injected as callables; `build_tools()` + `ask()` wire
   the real store/schema/execution.
3. `app/config.py` — `statement_timeout_ms`.
4. Tests: `test_agent.py` (stub LLM: happy path, **self-correction after a SQL error**, iteration cap,
   general answer, unknown tool) + a live end-to-end integration test; `test_execution.py` (integration:
   rejects non-SELECT, returns DB errors, enforces LIMIT + truncation).

## Done when
- [x] The loop drives search_schema → run_sql → answer, bounded by `agent_max_iterations`; returns the
      answer + a trace (tool calls, SQL) + summed token/cost usage.
- [x] A SQL error or empty result is fed back and the loop can retry (tested with a stub).
- [x] `run_sql` is hardened: read-only user + validator + LIMIT + statement timeout + row cap; returns
      structured errors (tested against live MySQL).
- [x] Unit gates green (90); full suite incl. live MySQL = 107; live end-to-end answers a real question.

---
Log → [`discussion.md`](discussion.md)
