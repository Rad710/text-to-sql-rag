---
status: done
updated: 2026-08-10
depends_on: [0001]
decision: 0003
---

# 0004 — SQL safety layer (validator + enforced LIMIT)

## Goal
The security-critical core: given model-written SQL, guarantee it is a single read-only `SELECT` and that
every result set is bounded — **in code, not by prompting**. Two pure, heavily-tested modules that become
the guardrails on the `run_sql` tool (task 0008).

## Context
Governed by [decision 0003](../../decisions/0003-sql-safety-defense-in-depth.md) (layers 2 + 3). We beat
both reference repos here: **`sqlglot` AST validation** instead of a regex/keyword denylist (fewer false
accepts/rejects; literal- and comment-hidden payloads can't fool it), and a **code-enforced `LIMIT`**
instead of a prompt instruction. Layers 1 (read-only DB user) and 4 (connection hardening: read-only
session, statement timeout, row cap) land elsewhere — the user is done ([0002](../0002-synthetic-mysql-db/)),
the connection hardening ships with the execution path in the engine (0005/0008).

## Plan
1. `app/validator.py` — `validate_read_only(sql, dialect="mysql") -> str`: parse with sqlglot; require a
   single statement whose root is `SELECT`/set-op; reject any DML/DDL/`Command`/`SET`/`INTO` node anywhere
   in the tree (catches data-modifying CTEs, `SELECT … INTO OUTFILE`) and a denylist of dangerous
   functions (`sleep`, `benchmark`, `load_file`, …). Returns normalized SQL. Raises `ValidationError`.
2. `app/limits.py` — `enforce_limit(sql, max_rows, dialect="mysql") -> str`: add a `LIMIT` if absent,
   clamp it if larger than `max_rows`, leave a smaller one untouched — via AST rewrite.
3. `tests/test_validator.py` — large allow-list / block-list suite (CTEs, unions, literal-hidden keywords,
   stacked statements, `INTO OUTFILE`, `sleep()`, `SET`, empty/garbage).
4. `tests/test_limits.py` — absent/smaller/equal/larger limit cases + ORDER BY.

## Done when
- [x] `validate_read_only` accepts legitimate SELECT/CTE/UNION (incl. keyword-in-literal) and rejects every
      write/DDL/multi-statement/`INTO OUTFILE`/dangerous-function case — 24 parametrized cases.
- [x] `enforce_limit` injects `LIMIT max_rows` when absent, clamps an over-large one, preserves a smaller
      one — 7 cases (incl. ORDER BY / WHERE).
- [x] Both modules pure (stdlib + sqlglot only); ruff/mypy clean; unit suite now 53 passing.

---
Log → [`discussion.md`](discussion.md)
