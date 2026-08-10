# 0012 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: **Execution accuracy, not string match** — compare the *result sets* of the agent's SQL and
  an independent gold SQL. The comparison is a multiset of rows, each row a sorted tuple of string values,
  so it's insensitive to row order AND column order (a real LLM may alias/reorder columns). "It executed
  without error" is explicitly rejected as a vanity metric.
- 2026-08-10: Gold SQL is written independently where natural (e.g. `revenue_per_route` groups by
  origin/destination, not route_code — same rows for this seed; `weight_loss` uses `SUM(a)-SUM(b)` vs
  `SUM(a-b)`), so the mock-mode 100% is a real check that the *example corpus* is correct, not a tautology.
  One case (`expenses_with_without_receipt`) must share the CASE labels, since the output labels are part
  of the intended answer — kept identical there.
- 2026-08-10: In mock mode the eval is a pipeline/regression guard (100%, in CI). A true model-accuracy
  number needs `LLM_MODE=openai` + a key: `python -m evaluation.runner`. `evaluation/` is a top-level
  package (not `eval`, which shadows the builtin). 8/8 verified against the live DB.
