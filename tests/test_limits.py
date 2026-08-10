"""Tests for code-enforced LIMIT injection/clamping."""

from __future__ import annotations

import re

import pytest

from app.limits import enforce_limit


def _limit_of(sql: str) -> int | None:
    m = re.search(r"limit\s+(\d+)", sql, re.IGNORECASE)
    return int(m.group(1)) if m else None


def test_adds_limit_when_absent() -> None:
    assert _limit_of(enforce_limit("SELECT * FROM shipment", 500)) == 500


def test_clamps_over_large_limit() -> None:
    assert _limit_of(enforce_limit("SELECT * FROM shipment LIMIT 1000", 500)) == 500


def test_preserves_smaller_limit() -> None:
    assert _limit_of(enforce_limit("SELECT * FROM shipment LIMIT 10", 500)) == 10


def test_preserves_equal_limit() -> None:
    assert _limit_of(enforce_limit("SELECT * FROM shipment LIMIT 500", 500)) == 500


def test_adds_limit_after_order_by() -> None:
    out = enforce_limit("SELECT origin, price FROM shipment ORDER BY price DESC", 500)
    assert _limit_of(out) == 500
    assert "order by" in out.lower()


def test_clamps_with_existing_clauses() -> None:
    out = enforce_limit("SELECT * FROM shipment WHERE deleted = 0 LIMIT 99999", 500)
    assert _limit_of(out) == 500


def test_rejects_non_positive_max() -> None:
    with pytest.raises(ValueError):
        enforce_limit("SELECT 1", 0)
