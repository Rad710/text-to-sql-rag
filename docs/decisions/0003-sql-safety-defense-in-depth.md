---
status: accepted
date: 2026-08-10
---

# 0003 — Enforce read-only SQL in depth: DB user + sqlglot + LIMIT + connection hardening

## Context
The assistant executes **model-written SQL** inside an agentic loop that may run many queries per question.
A single missed guard could let a prompt-injected or hallucinated statement mutate or exfiltrate data. The
reference implementations rely on regex/keyword denylists and a read-only DB user, and enforce `LIMIT` only
by prompting — both are bypassable in edge cases.

## Decision
We will enforce read-only in **four independent layers**, and never weaken one to make a query pass:

1. **DB-level read-only user** — the app connects to MySQL as a user with `SELECT`-only grants. This is the
   true guarantee; a full validator bypass still cannot write.
2. **`sqlglot` AST validation** — parse the statement with the MySQL dialect; require exactly one
   `SELECT`/CTE; reject any DML/DDL node, multiple statements, and dangerous functions/`INTO`. Run at both
   the tool layer and the execute layer (defense in depth). This beats the references' regex denylist —
   fewer false rejects of legit identifiers, fewer false accepts.
3. **Code-enforced `LIMIT`** — inject or clamp a `LIMIT` in code (not by prompting), so every result set is
   bounded regardless of what the model wrote.
4. **Connection hardening** — read-only session, `statement_timeout`/`MAX_EXECUTION_TIME`, a row cap
   (fetch cap+1 to detect truncation), and a fresh connection per query (no pool carry-over).

If a legitimate query is blocked, we fix the validator **with a test**, never by removing a check.

## Consequences
- Good: multiple independent gates; AST-level validation is precise and testable as a pure function; bounded
  cost per query; the DB user is the real backstop.
- Bad / cost: `sqlglot` is a dependency and must track the MySQL dialect; enforcing `LIMIT` means rewriting
  the AST (careful with existing `LIMIT`/aggregates).

## Alternatives considered
- **Regex/keyword denylist** (references' approach) — simple but false-rejects identifiers named like
  keywords and can be fooled by literals/comments; rejected in favour of AST parsing.
- **DB read-only user alone** — necessary but not sufficient: it can't cap rows/time or give friendly
  validation errors to the agent loop.
