# 0036 — discussion

Append-only. Newest at the bottom, each entry dated. Options weighed, decisions, open questions, dead
ends — the thinking behind the spec. Keeps [`README.md`](README.md) clean.

- 2026-08-12: **Diagnosis (live Playwright pass).** With `llama3.1:8b`, ~half of data questions gave
  wrong answers. Expanding the `run_sql` step showed the model had written good SQL but named the argument
  `sql` (e.g. `{"sql":"SELECT driver_name, COUNT(*) …"}`) → backend read `arguments["query"]` (empty) →
  validator `ERROR: rejected: empty SQL` → the model invented "no data" prose. When the same model
  happened to name it `query`, the identical question worked. So it's arg-name non-determinism, not the
  reorg and not general model weakness.

- 2026-08-12: **Fix choice.** Accept `sql` as an alias for `query` rather than (a) prompt-nagging the model
  to use `query` (unreliable) or (b) switching models. Safe: the sqlglot validator + read-only user still
  enforce everything; both keys are just the SQL string. Added a small `_sql_arg()` helper used at both
  extraction points. Also fixed the frontend `argsText` fallback so the step renders bare SQL instead of
  raw `{"sql":…}` JSON when the model used `sql`.

- 2026-08-12: **Verified live (extensive).** Restarted the API with the fix (live, llama3.1:8b) and
  re-ran through the browser: the exact driver-aggregation query that failed twice now returns the correct
  table (Juan/María/Carlos/Ana, trips + kg) and answer — the model again used `sql`, now accepted, and the
  step shows bare SQL. Also confirmed: route billing (bar chart), driver count, a `shipment_payroll` JOIN
  for unpaid settlements (2 rows, correct totals), and general chit-chat ("hello how are you" → polite
  prose, no tool call; a capabilities question → search_schema + a good bulleted list). 0 console errors
  throughout. Backend suite 129 green + ruff/mypy; frontend lint + build + 22 tests green.

- 2026-08-12: **Left for later (not done here):** `search_schema` still reads only `question`; it hasn't
  misbehaved in testing, so left as-is to keep the change minimal. If a model names it `query`, the same
  alias approach would apply.
