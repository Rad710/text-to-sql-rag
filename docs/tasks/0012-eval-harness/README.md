---
status: done
updated: 2026-08-10
depends_on: [0008]
decision: null
---

# 0012 — Evaluation harness (execution accuracy) + failure modes

## Goal
Measure the assistant, don't just demo it: a golden `(question → gold SQL)` set over the freight DB and an
**execution-accuracy** runner (compare *result sets*, not SQL strings) wired into CI, plus a documented list
of failure modes. This is the single highest-signal artifact — most projects show "it works" and never "how
well / where it breaks."

## Context
The gold SQL is written independently of the corpus examples but must return the same result set as the
correct answer, so the harness scores **semantics**. In mock mode it is a pipeline + example-corpus
regression guard (100%); against a real LLM (`LLM_MODE=openai`) it reports true accuracy.

## Plan
1. `evaluation/cases.py` — `EvalCase` + 8 gold cases (the canonical freight questions, EN/ES).
2. `evaluation/runner.py` — `run_eval` (run the agent → execute its SQL + the gold SQL → compare result
   sets, order-insensitive over rows/columns) + `format_report` + `python -m evaluation.runner`.
3. `tests/test_eval.py` — pure tests for the comparison + an `@integration` test asserting **100%** in
   mock mode (regression guard; runs in the integration CI job).
4. `docs/failure-modes.md` — where it breaks (ambiguity, wrong joins, silently-wrong filters, …) and what's
   guarded (writes, runaway queries).
5. `mypy app evaluation` in CI + CLAUDE.md.

## Done when
- [x] `python -m evaluation.runner` prints a per-case table + overall accuracy; **8/8 = 100%** in mock mode.
- [x] Execution accuracy compares result sets (not SQL text), order-insensitive over rows and columns.
- [x] Wired into CI (integration job asserts 100% mock accuracy); `evaluation` type-checked.
- [x] `docs/failure-modes.md` documents the failure modes + the guardrails. Gates green (99 unit + 19 int).

---
Log → [`discussion.md`](discussion.md)
