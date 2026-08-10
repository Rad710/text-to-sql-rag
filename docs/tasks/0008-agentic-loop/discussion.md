# 0008 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Tools are injected into the loop as plain callables (`search_schema: str->str`,
  `run_sql: str->RunResult`), so the loop unit-tests with stubs — no DB, no network. `run_sql` returns a
  structured `RunResult` and **never raises** on a bad query, which is what makes self-correction possible:
  the error string is fed straight back as the tool result and the model revises.
- 2026-08-10: **Truncation-detection bug** — the injected `LIMIT` caps the fetch at `result_limit`, so the
  old "fetch limit+1" could never exceed it and `truncated` was always False. Fixed: truncated =
  `len(rows) >= result_limit` (hitting the cap means rows may have been dropped). Caught by the integration
  test with `result_limit=5`.
- 2026-08-10: **utf8mb4 bug** — driver "María" rendered as "MarÃ­a". Root cause was the seed being loaded by
  a non-utf8mb4 init client (stored double-encoded, 6 chars). Fixed at the source: `SET NAMES utf8mb4;` at
  the top of `01_schema.sql`/`02_seed.sql`, plus `charset="utf8mb4"` on the pymysql connections. Re-seeded;
  now stored as 5 chars and renders correctly end to end.
