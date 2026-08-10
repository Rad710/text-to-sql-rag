"""Code-enforced ``LIMIT`` via sqlglot AST rewrite (decision 0003, layer 3).

Every result set is bounded in code — never by prompting the model. Add a ``LIMIT`` when absent,
clamp one larger than ``max_rows``, and leave a smaller one untouched. Pure and unit-tested.

Call *after* :func:`app.validator.validate_read_only`, which guarantees a single valid query.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp


def enforce_limit(sql: str, max_rows: int, dialect: str = "mysql") -> str:
    """Return ``sql`` with a ``LIMIT`` of at most ``max_rows``."""
    if max_rows <= 0:
        raise ValueError("max_rows must be positive")

    stmt = sqlglot.parse_one(sql, read=dialect)
    if not isinstance(stmt, exp.Query):
        return stmt.sql(dialect=dialect)

    existing = stmt.args.get("limit")
    if existing is None:
        stmt = stmt.limit(max_rows)
    else:
        value = existing.expression
        if isinstance(value, exp.Literal) and not value.is_string:
            try:
                current = int(value.name)
            except ValueError:
                current = None
            if current is not None and current > max_rows:
                stmt = stmt.limit(max_rows)

    return stmt.sql(dialect=dialect)
