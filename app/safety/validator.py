"""Read-only SQL validation via sqlglot AST parsing.

The security-critical gate on model-written SQL (decision 0003, layer 2). AST-based rather than a
regex/keyword denylist: keywords hidden in string literals or comments can't fool it, and legitimate
identifiers that merely *look* like keywords aren't false-rejected. Pure — no I/O — so it unit-tests
exhaustively without a database.

A statement passes only if it is a **single** query whose root is a `SELECT`/set-operation, contains
**no** DML/DDL/command/`INTO` node anywhere in the tree (so a data-modifying CTE or `SELECT … INTO
OUTFILE` is caught), and calls no dangerous function. Returns the normalized SQL.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError


class ValidationError(ValueError):
    """Raised when SQL is not a safe, single read-only SELECT."""


# Any of these appearing anywhere in the tree is a hard reject.
_FORBIDDEN_NODE_NAMES = (
    "Insert",
    "Update",
    "Delete",
    "Drop",
    "Create",
    "Alter",
    "TruncateTable",
    "Command",  # catch-all sqlglot uses for unparsed / DDL-ish statements
    "Set",
    "Into",  # SELECT … INTO OUTFILE / INTO @var
    "Use",
    "Merge",
    "Grant",
)
_FORBIDDEN_NODES = tuple(getattr(exp, name) for name in _FORBIDDEN_NODE_NAMES if hasattr(exp, name))

# DoS / filesystem / lock functions that have no place in an analytics read.
_FORBIDDEN_FUNCTIONS = frozenset(
    {
        "sleep",
        "benchmark",
        "load_file",
        "get_lock",
        "release_lock",
        "master_pos_wait",
        "sys_exec",
        "sys_eval",
    }
)


def validate_read_only(sql: str, dialect: str = "mysql") -> str:
    """Return normalized SQL if it is a single read-only SELECT, else raise ``ValidationError``."""
    if not sql or not sql.strip():
        raise ValidationError("empty SQL")

    try:
        statements = [s for s in sqlglot.parse(sql, read=dialect) if s is not None]
    except SqlglotError as exc:
        raise ValidationError(f"could not parse SQL: {exc}") from exc

    if not statements:
        raise ValidationError("no SQL statement found")
    if len(statements) > 1:
        raise ValidationError("multiple statements are not allowed")

    stmt = statements[0]
    if not isinstance(stmt, exp.Query):
        raise ValidationError(
            f"only read-only SELECT queries are allowed (got {type(stmt).__name__})"
        )

    forbidden = next(stmt.find_all(*_FORBIDDEN_NODES), None)
    if forbidden is not None:
        raise ValidationError(f"forbidden SQL construct: {type(forbidden).__name__}")

    for func in stmt.find_all(exp.Anonymous):
        name = func.this.lower() if isinstance(func.this, str) else ""
        if name in _FORBIDDEN_FUNCTIONS:
            raise ValidationError(f"forbidden function: {name}()")

    # comments are already parsed away for safety; drop them from the normalized output too.
    return stmt.sql(dialect=dialect, comments=False)
