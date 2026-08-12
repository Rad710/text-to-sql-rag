"""Exhaustive allow-list / block-list for the read-only SQL validator."""

from __future__ import annotations

import pytest

from app.safety.validator import ValidationError, validate_read_only

ALLOWED = [
    "SELECT 1",
    "SELECT * FROM shipment",
    "select price from shipment where deleted = 0",
    "SELECT origin, SUM(price) FROM shipment GROUP BY origin ORDER BY 2 DESC",
    "SELECT s.price, d.driver_name FROM shipment s JOIN driver d USING (driver_code)",
    "WITH t AS (SELECT 1 AS x) SELECT x FROM t",
    "SELECT 1 UNION SELECT 2",
    "SELECT COUNT(*) FROM shipment WHERE shipment_date >= '2026-01-01'",
    # a keyword hidden in a string literal must NOT trip the validator:
    "SELECT * FROM driver WHERE driver_name = 'DROP TABLE shipment'",
    # trailing semicolon / whitespace is a single statement:
    "SELECT 1;",
    "  SELECT 1  ",
    # a column literally named like a keyword is fine:
    "SELECT created_at FROM shipment",
]

BLOCKED = [
    "",
    "   ",
    "banana",
    "INSERT INTO product (product_name, modification_user) VALUES ('x', 'y')",
    "UPDATE driver SET driver_name = 'x' WHERE driver_code = 1",
    "DELETE FROM shipment WHERE shipment_code = 1",
    "DROP TABLE shipment",
    "CREATE TABLE evil (id INT)",
    "ALTER TABLE shipment ADD COLUMN evil INT",
    "TRUNCATE TABLE shipment",
    "SELECT 1; DROP TABLE shipment",  # stacked statements
    "SELECT 1; SELECT 2",  # multiple statements
    "SET @x = 1",
    "USE mysql",
    "SELECT * INTO OUTFILE '/tmp/x.txt' FROM shipment",
    "SELECT SLEEP(10)",
    "SELECT BENCHMARK(1000000, MD5('x'))",
    "SELECT LOAD_FILE('/etc/passwd')",
    # data-modifying CTE (Postgres-style) — blocked (nested DELETE or parse error):
    "WITH x AS (DELETE FROM shipment RETURNING *) SELECT * FROM x",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_allowed_queries_pass(sql: str) -> None:
    out = validate_read_only(sql)
    assert out  # returns normalized, non-empty SQL
    assert "select" in out.lower()


@pytest.mark.parametrize("sql", BLOCKED)
def test_blocked_queries_raise(sql: str) -> None:
    with pytest.raises(ValidationError):
        validate_read_only(sql)


def test_normalizes_and_strips_comments() -> None:
    out = validate_read_only("SELECT 1 -- a trailing comment")
    assert "comment" not in out.lower()


def test_returns_single_statement_without_semicolon() -> None:
    assert validate_read_only("SELECT 1;").strip().endswith("1")
