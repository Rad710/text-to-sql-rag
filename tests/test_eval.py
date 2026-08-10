"""Tests for the evaluation harness."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.cases import GOLD_CASES
from evaluation.runner import _normalize, format_report, run_eval


def test_normalize_is_row_and_column_order_insensitive() -> None:
    assert _normalize([(1, "x"), (2, "y")]) == _normalize([("y", 2), ("x", 1)])


def test_normalize_distinguishes_values() -> None:
    assert _normalize([(1, 2)]) != _normalize([(1, 3)])


@pytest.mark.integration
def test_mock_execution_accuracy_is_100(tmp_path: Path) -> None:
    """In mock mode the gold set must score 100% — a pipeline + example-corpus regression guard."""
    import pymysql

    from app.corpus import build_corpus
    from app.embeddings import OfflineEmbedder
    from app.engine import RagStore
    from app.introspect import introspect_from_settings

    try:
        schema = introspect_from_settings()
    except pymysql.MySQLError as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no MySQL reachable: {exc}")

    store = RagStore(path=str(tmp_path), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(schema))
    report = run_eval(GOLD_CASES, store=store, schema=schema)
    assert report.accuracy == 1.0, format_report(report)
