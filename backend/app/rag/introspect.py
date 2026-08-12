"""Read the live database schema from ``information_schema`` into a :class:`SchemaInfo`.

Thin and impure — the only DB-touching part of the schema pipeline. All rendering lives in the
pure :mod:`app.schema`. Run ``python -m app.introspect`` to print the annotated DDL.
"""

from __future__ import annotations

from typing import Any

import pymysql

from app.config import get_settings
from app.rag.schema import Column, ForeignKey, SchemaInfo, Table

_COLUMNS_SQL = """
    SELECT table_name, column_name, column_type, is_nullable, column_key
    FROM information_schema.columns
    WHERE table_schema = %s
    ORDER BY table_name, ordinal_position
"""

_BASE_TABLES_SQL = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = %s AND table_type = 'BASE TABLE'
"""

# The business tables the assistant exposes (mirrors the seed in mock-db/migration/). A real DB may
# also hold audit / framework / legacy tables (`*_audit`, `alembic_version`, `user`, older tables);
# introspection ignores anything outside this set so the LLM only ever sees the modelled schema.
BUSINESS_TABLES: frozenset[str] = frozenset(
    {
        "driver",
        "route",
        "product",
        "shipment",
        "shipment_expense",
        "shipment_payroll",
        "driver_payroll",
    }
)

_FK_SQL = """
    SELECT table_name, column_name, referenced_table_name, referenced_column_name
    FROM information_schema.key_column_usage
    WHERE table_schema = %s AND referenced_table_name IS NOT NULL
"""


def introspect(conn: Any, schema_name: str) -> SchemaInfo:
    """Build a :class:`SchemaInfo` for ``schema_name`` from an open DB connection."""
    columns_by_table: dict[str, list[Column]] = {}
    with conn.cursor() as cur:
        cur.execute(_COLUMNS_SQL, (schema_name,))
        for table_name, col_name, col_type, is_nullable, col_key in cur.fetchall():
            columns_by_table.setdefault(table_name, []).append(
                Column(
                    name=col_name,
                    data_type=col_type,
                    nullable=(is_nullable == "YES"),
                    is_primary_key=(col_key == "PRI"),
                )
            )

    with conn.cursor() as cur:
        cur.execute(_BASE_TABLES_SQL, (schema_name,))
        base_tables = {row[0] for row in cur.fetchall() if row[0] in BUSINESS_TABLES}

    fks_by_table: dict[str, list[ForeignKey]] = {}
    with conn.cursor() as cur:
        cur.execute(_FK_SQL, (schema_name,))
        for table_name, col_name, ref_table, ref_col in cur.fetchall():
            fks_by_table.setdefault(table_name, []).append(
                ForeignKey(column=col_name, ref_table=ref_table, ref_column=ref_col)
            )

    tables = tuple(
        Table(
            name=name,
            columns=tuple(columns_by_table.get(name, [])),
            foreign_keys=tuple(fks_by_table.get(name, [])),
        )
        for name in sorted(base_tables)
    )
    return SchemaInfo(tables=tables)


def introspect_from_settings() -> SchemaInfo:
    """Open a connection from the app settings and introspect the configured schema."""
    s = get_settings()
    conn = pymysql.connect(
        host=s.query_db_host,
        port=s.query_db_port,
        user=s.query_db_user,
        password=s.query_db_password,
        database=s.query_db_name,
        charset="utf8mb4",
        connect_timeout=5,
    )
    try:
        return introspect(conn, s.query_db_name)
    finally:
        conn.close()


if __name__ == "__main__":  # pragma: no cover - manual convenience
    from app.rag.schema import render_schema_ddl

    print(render_schema_ddl(introspect_from_settings()))
