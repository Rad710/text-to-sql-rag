# 0004 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Scoped to the two **pure** modules (validator + limits). Connection-level hardening
  (read-only session / statement timeout / row cap — layer 4 of [decision 0003](../../decisions/0003-sql-safety-defense-in-depth.md))
  is deliberately deferred to the execution path in the engine (0005/0008), where the connection lives.
- 2026-08-10: Validation strategy = **AST, not regex**. Require the root to be a SELECT/set-op AND scan the
  whole tree for forbidden node types — a root check alone would miss a data-modifying CTE
  (`WITH x AS (DELETE …) SELECT …`) or `SELECT … INTO OUTFILE`.
- 2026-08-10: Built on sqlglot 30.16. Root check = `isinstance(stmt, exp.Query)` (covers Select + set-ops);
  forbidden-node scan via `find_all` over Insert/Update/Delete/Drop/Create/Alter/TruncateTable/Command/Set/
  Into/Use/Merge/Grant; dangerous-function denylist over `exp.Anonymous` (sleep/benchmark/load_file/…).
  `validate_read_only` returns normalized SQL with `comments=False` (sqlglot preserves comments otherwise).
  `enforce_limit` uses `exp.Query.limit()` + literal clamp. 53 unit tests green; live sanity-checked. Done.
