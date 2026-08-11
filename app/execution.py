"""The `run_sql` tool: validate → enforce LIMIT → execute read-only, hardened.

This is where the SQL-safety layers compose against a live connection (decision 0003):
validate (layer 2, 0004) → enforce LIMIT (layer 3, 0004) → execute as the read-only user (layer 1,
0002) on a **fresh connection** with a **statement timeout** and a **row cap** (layer 4, here).

Returns a structured :class:`RunResult` (never raises for a bad query) so the agent loop can feed
the error or rows back to the model and self-correct.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import Settings, get_settings
from app.limits import enforce_limit
from app.validator import ValidationError, validate_read_only


@dataclass(frozen=True, slots=True)
class RunResult:
    sql: str  # the SQL actually sent (post validation + LIMIT)
    columns: list[str] = field(default_factory=list)
    rows: list[tuple[Any, ...]] = field(default_factory=list)
    truncated: bool = False
    error: str | None = None

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def as_cells(self, max_rows: int = 100) -> list[list[str]]:
        """Rows as JSON-safe string cells — the structured payload the frontend renders."""
        return [["NULL" if v is None else str(v) for v in row] for row in self.rows[:max_rows]]


def run_sql(query: str, settings: Settings | None = None) -> RunResult:
    """Validate, bound, and execute ``query`` read-only; return rows or a structured error."""
    s = settings or get_settings()

    try:
        safe = validate_read_only(query)
    except ValidationError as exc:
        return RunResult(sql=query, error=f"rejected: {exc}")

    bounded = enforce_limit(safe, s.result_limit)

    import pymysql

    try:
        conn = pymysql.connect(
            host=s.db_host,
            port=s.db_port,
            user=s.db_user,
            password=s.db_password,
            database=s.db_name,
            charset="utf8mb4",
            connect_timeout=5,
            read_timeout=max(1, s.statement_timeout_ms // 1000 + 1),
            autocommit=True,
        )
    except pymysql.MySQLError as exc:  # pragma: no cover - environment-dependent
        return RunResult(sql=bounded, error=f"connection error: {exc}")

    try:
        with conn.cursor() as cur:
            cur.execute("SET SESSION max_execution_time = %s", (s.statement_timeout_ms,))
            cur.execute(bounded)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = [tuple(r) for r in cur.fetchall()]
        # `bounded` caps the fetch at result_limit; hitting it means rows may have been dropped.
        truncated = len(rows) >= s.result_limit
        return RunResult(sql=bounded, columns=columns, rows=rows, truncated=truncated)
    except pymysql.MySQLError as exc:
        return RunResult(sql=bounded, error=str(exc))
    finally:
        conn.close()


def format_result(result: RunResult, max_rows: int = 50) -> str:
    """Serialize a :class:`RunResult` as a compact Markdown table for the **model** to read.

    This is the model-facing tool-message text only; the UI renders the table from the structured
    rows on the SSE ``tool_result`` event (decision 0006), not from this string.
    """
    if result.error:
        return f"ERROR: {result.error}"
    if not result.rows:
        return "(0 rows)"

    def esc(cell: str) -> str:  # a pipe in a value would break the Markdown row
        return cell.replace("|", "\\|")

    header = "| " + " | ".join(esc(c) for c in result.columns) + " |"
    separator = "| " + " | ".join("---" for _ in result.columns) + " |"
    body = ["| " + " | ".join(esc(c) for c in row) + " |" for row in result.as_cells(max_rows)]
    note = f"({result.row_count} rows{', truncated' if result.truncated else ''})"
    return "\n".join([header, separator, *body]) + "\n\n" + note
