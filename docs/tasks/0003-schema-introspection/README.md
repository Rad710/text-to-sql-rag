---
status: done
updated: 2026-08-10
depends_on: [0002]
decision: null
---

# 0003 — Schema introspection → annotated DDL

## Goal
Turn the live database into the **single source of truth** for the RAG layer: introspect
`information_schema` and render annotated `CREATE TABLE` DDL (with FK-derived `-- joins:` annotations) plus
compact one-line table summaries. This is what task 0005 indexes and the `search_schema` tool serves — no
hand-duplicated DDL (the weakness in both reference repos).

## Context
See [`../../architecture.md`](../../architecture.md) (RAG section — relationship-following via join
annotations + two-tier schema presentation) and [`../../reference.md`](../../reference.md) (the schema).
Keep the rendering **pure** (schema model → strings, unit-tested without a DB); keep the DB read in a thin
impure module.

## Plan
1. `app/schema.py` — **pure**: dataclasses (`Column`, `ForeignKey`, `Table`, `SchemaInfo`) + renderers:
   annotated DDL per table (`-- joins:` line from FKs both directions + `PRIMARY KEY`/`FOREIGN KEY`), a
   compact summary (`name(col type PK, col type ->ref, …)` with a column cap), and a whole-schema dump.
2. `app/introspect.py` — **impure**: read `information_schema.columns` / `.key_column_usage` / `.tables`
   into a `SchemaInfo`; `introspect_from_settings()` opens a connection from config. `python -m app.introspect`
   prints the rendered DDL.
3. `tests/test_schema.py` — pure unit tests (hand-built schema): join annotations both directions, DDL
   shape, summary format + truncation.
4. `tests/test_introspect.py` — `@integration`: introspect the live DB → 7 tables, `shipment` has the 5
   expected FKs, rendered DDL carries `-- joins:`.
5. `pyproject.toml` — mypy override for `pymysql.*` (no stubs).

## Done when
- [x] `app/schema.py` renders annotated DDL + summaries from a `SchemaInfo`, pure and unit-tested
      (5 unit tests; total unit suite 13).
- [x] `app/introspect.py` builds a `SchemaInfo` from the live DB; `python -m app.introspect` prints the
      annotated DDL (verified).
- [x] FK `-- joins:` annotations are correct in both directions — e.g. `driver → driver_payroll, shipment`
      and `shipment → driver, product, route, shipment_payroll, driver_payroll`.
- [x] Unit gates green; 3 introspection integration tests pass against the live MySQL (9 integration total).

---
Log → [`discussion.md`](discussion.md)
