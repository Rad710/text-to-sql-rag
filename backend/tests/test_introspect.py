"""Integration: introspect the live synthetic DB and check the generated schema/DDL.

Opt-in (``integration`` marker). Needs a live MySQL with the init SQL applied.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pymysql
import pytest

from app.config import get_settings
from app.rag.introspect import introspect
from app.rag.schema import render_schema_ddl

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
SHIPMENT_FK_TARGETS = {"driver", "product", "route", "shipment_payroll", "driver_payroll"}


@pytest.fixture(scope="module")
def conn() -> Iterator[Any]:
    s = get_settings()
    try:
        connection = pymysql.connect(
            host=s.db_host,
            port=s.db_port,
            user=s.db_user,
            password=s.db_password,
            database=s.db_name,
            connect_timeout=5,
        )
    except pymysql.MySQLError as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no MySQL reachable ({s.db_host}:{s.db_port}): {exc}")
    yield connection
    connection.close()


def test_introspect_finds_all_business_tables(conn: Any) -> None:
    schema = introspect(conn, get_settings().db_name)
    assert {t.name for t in schema.tables} == EXPECTED_TABLES


def test_shipment_foreign_keys_and_joins(conn: Any) -> None:
    schema = introspect(conn, get_settings().db_name)
    shipment = schema.table("shipment")
    assert shipment is not None
    assert {fk.ref_table for fk in shipment.foreign_keys} == SHIPMENT_FK_TARGETS
    # Every FK target is a join partner (fact → dimension).
    assert set(schema.join_partners("shipment")) >= SHIPMENT_FK_TARGETS
    # And the dimensions see the fact table back (dimension → fact).
    assert "shipment" in schema.join_partners("driver")


def test_rendered_ddl_covers_schema(conn: Any) -> None:
    schema = introspect(conn, get_settings().db_name)
    ddl = render_schema_ddl(schema)
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE {table} (" in ddl
    assert "-- joins:" in ddl
    assert "FOREIGN KEY (driver_code) REFERENCES driver(driver_code)" in ddl
