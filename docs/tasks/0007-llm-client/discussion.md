# 0007 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Messages use the **OpenAI chat format** (list of role dicts) as the lingua franca — the real
  provider passes them straight through, and the mock inspects them. The mock is a **state machine over the
  history** (which tool calls have already been made), not a turn counter, so it composes with the agent
  loop without shared state. Canned SQL comes from reusing `app.corpus.EXAMPLES` (one source of truth →
  the validator invariant holds for free). Cost is estimated from configurable per-1M-token prices
  (default 0.0 — unknown pricing shows as $0, never a wrong number).
- 2026-08-10: Built + verified. `MockProvider`/`OpenAIProvider` behind `LlmProvider`; `Usage` carries
  tokens + cost and is addable (the loop sums per-turn usage). openai 2.53 installed; types resolve (no
  mypy override needed). Live check: mock emits search_schema then run_sql (correct canned SQL for the
  driver question) with usage reported. 10 unit tests; 85 total. Done.
