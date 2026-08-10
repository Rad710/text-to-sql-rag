# 0003 — discussion

Append-only. Newest at the bottom, each entry dated.

- 2026-08-10: Split pure rendering (`app/schema.py`) from the DB read (`app/introspect.py`) per the
  pure/impure discipline — the renderers unit-test with a hand-built `SchemaInfo`, no DB needed. `-- joins:`
  annotations are computed **both directions** (a table's own FKs *and* the tables that FK to it), so
  retrieval can follow a dimension → fact edge as well as fact → dimension.
- 2026-08-10: Built + verified. `python -m app.introspect` renders correct annotated DDL against the live
  DB (e.g. `driver` shows `-- joins: driver_payroll, shipment`). Added a mypy override for `pymysql.*`
  (no bundled stubs). Gates green (13 unit); 9 integration tests pass (3 new introspection). Done.
