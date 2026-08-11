---
status: accepted
date: 2026-08-11
---

# 0006 — Stream structured query results; the frontend owns table presentation

## Context
The `run_sql` result was rendered for the UI by the **backend**: `format_result` produced a text
table, the mock echoed it into the `answer`, and the frontend rendered that text as Markdown. So the
browser's table depended on backend string formatting — a presentation concern living in the wrong
layer (and the source of a Markdown setext-heading bug). A model-facing *text* serialization must
exist (the LLM reads tool results as text), but the **UI** should not depend on it.

## Decision
We will separate the two consumers of a query result:

- **Model-facing:** `format_result` remains a neutral text serialization read by the LLM as the tool
  message. It is no longer used to render the UI.
- **UI-facing:** the SSE `tool_result` event for `run_sql` carries **structured** data —
  `columns: string[]`, `rows: string[][]` (cells stringified, capped), `row_count`, `truncated`. The
  **frontend** renders the table itself (a real React table in the `run_sql` tool step). The mock's
  `answer` becomes plain prose; it no longer embeds the result table.

## Consequences
- Good: correct layering — the backend emits data, the frontend owns presentation; the UI table is a
  real component fed structured rows, not parsed backend Markdown; the model still gets clean text.
- Good: satisfies decision 0005's "tool-call rendering … SQL → results" with the results as structured
  rows in the step.
- Bad / cost: the SSE payload for `run_sql` grows (rows are included, capped); one more event shape the
  frontend must handle; the mock answer is now a short canned prose line (deterministic, not eloquent).

## Alternatives considered
- **Keep backend Markdown, render as Markdown in the UI** — rejected: presentation in the backend, the
  layering smell this record fixes.
- **Frontend builds a Markdown table from the structured rows** — workable, but round-trips
  data→Markdown→parsed-table; a real table component fed structured rows is cleaner.
