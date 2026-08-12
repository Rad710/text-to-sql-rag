"""Integration checks against the synthetic MySQL demo DB.

Opt-in (marked ``integration``; excluded from the default run). Needs a live MySQL with the
init SQL applied — locally via ``docker compose up mysql``, in CI via the ``integration`` job.
Connects as the read-only app user and verifies the schema, the seed, and — most importantly —
that writes are rejected (decision 0003's real guarantee).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pymysql
import pytest

from app.config import get_settings

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    "driver",
    "route",
    "product",
    "shipment",
    "shipment_payroll",
    "driver_payroll",
    "shipment_expense",
}


@pytest.fixture(scope="module")
def conn() -> Iterator[pymysql.connections.Connection]:
    s = get_settings()
    try:
        connection = pymysql.connect(
            host=s.query_db_host,
            port=s.query_db_port,
            user=s.query_db_user,
            password=s.query_db_password,
            database=s.query_db_name,
            connect_timeout=5,
        )
    except pymysql.MySQLError as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no MySQL reachable ({s.query_db_host}:{s.query_db_port}): {exc}")
    yield connection
    connection.close()


def _scalar(conn: pymysql.connections.Connection, sql: str) -> Any:
    with conn.cursor() as cur:
        cur.execute(sql)
        row = cur.fetchone()
    return row[0] if row else None


def test_all_business_tables_exist(conn: pymysql.connections.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            (get_settings().db_name,),
        )
        tables = {r[0] for r in cur.fetchall()}
    assert tables >= EXPECTED_TABLES


def test_seed_data_is_present(conn: pymysql.connections.Connection) -> None:
    assert _scalar(conn, "SELECT COUNT(*) FROM shipment") > 0
    assert _scalar(conn, "SELECT COUNT(*) FROM driver") == 4
    # Query-ready for the canonical demo questions:
    assert _scalar(conn, "SELECT COUNT(*) FROM shipment_payroll WHERE collected = 0") > 0
    assert _scalar(conn, "SELECT COUNT(*) FROM driver_payroll WHERE paid = 0") > 0
    assert _scalar(conn, "SELECT COUNT(*) FROM shipment_expense WHERE receipt IS NULL") > 0
    # Dates are relative to now, so the current month has shipments.
    assert (
        _scalar(
            conn,
            "SELECT COUNT(*) FROM shipment WHERE shipment_date >= DATE_FORMAT(NOW(), '%Y-%m-01')",
        )
        > 0
    )


@pytest.mark.parametrize(
    "write_sql",
    [
        "INSERT INTO product (product_name, modification_user) VALUES ('hack', 'x')",
        "UPDATE driver SET driver_name = 'x' WHERE driver_code = 1",
        "DELETE FROM shipment WHERE shipment_code = 1",
        "CREATE TABLE evil (id INT)",
    ],
)
def test_readonly_user_cannot_write(conn: pymysql.connections.Connection, write_sql: str) -> None:
    with pytest.raises(pymysql.MySQLError) as exc_info, conn.cursor() as cur:
        cur.execute(write_sql)
    # 1142 = command denied; 1044/1045 = access denied to the database/user.
    assert exc_info.value.args[0] in {1142, 1044, 1045}
