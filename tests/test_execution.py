"""Integration tests for the run_sql execution tool (live MySQL)."""

from __future__ import annotations

import dataclasses

import pytest

from app.config import get_settings
from app.execution import format_result, run_sql

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def _require_db() -> None:
    probe = run_sql("SELECT 1 AS n")
    if probe.error and "connection error" in probe.error:
        pytest.skip("no MySQL reachable")


def test_valid_query_returns_rows() -> None:
    result = run_sql("SELECT COUNT(*) AS n FROM shipment WHERE deleted = 0")
    assert result.error is None
    assert result.columns == ["n"]
    assert result.rows[0][0] > 0


def test_non_select_is_rejected_before_execution() -> None:
    result = run_sql("DROP TABLE shipment")
    assert result.error is not None
    assert result.error.startswith("rejected:")


def test_db_error_is_returned_not_raised() -> None:
    result = run_sql("SELECT nonexistent_column FROM shipment")
    assert result.error is not None
    assert "Unknown column" in result.error


def test_limit_is_enforced_and_truncation_flagged() -> None:
    small = dataclasses.replace(get_settings(), result_limit=5)
    result = run_sql("SELECT shipment_code FROM shipment", small)
    assert result.error is None
    assert result.row_count <= 5
    assert result.truncated is True  # the seed has more than 5 shipments


def test_format_result_shapes() -> None:
    ok = run_sql("SELECT COUNT(*) AS n FROM shipment")
    assert "n" in format_result(ok)
    assert format_result(run_sql("DROP TABLE x")).startswith("ERROR:")
    empty = run_sql("SELECT shipment_code FROM shipment WHERE 1 = 0")
    assert format_result(empty) == "(0 rows)"
