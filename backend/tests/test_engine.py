"""ChromaDB-backed tests for the RAG store (local temp dir; no network, no MySQL)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pymysql import MySQLError

from app.rag.corpus import DOCS, EXAMPLES, build_corpus
from app.rag.embeddings import OfflineEmbedder
from app.rag.engine import RagStore
from app.rag.introspect import introspect_from_settings
from app.rag.schema import Column, ForeignKey, SchemaInfo, Table

DRIVER = Table(
    name="driver",
    columns=(Column("driver_code", "int", nullable=False, is_primary_key=True),),
)
SHIPMENT = Table(
    name="shipment",
    columns=(
        Column("shipment_code", "int", nullable=False, is_primary_key=True),
        Column("driver_code", "int", nullable=False),
    ),
    foreign_keys=(ForeignKey("driver_code", "driver", "driver_code"),),
)
SCHEMA = SchemaInfo(tables=(DRIVER, SHIPMENT))


def _store(tmp_path: Path) -> RagStore:
    return RagStore(path=str(tmp_path), embedder=OfflineEmbedder())


def test_sync_adds_all_items(tmp_path: Path) -> None:
    store = _store(tmp_path)
    stats = store.sync_corpus(build_corpus(SCHEMA))
    assert stats["ddl"]["added"] == 2
    assert stats["documentation"]["added"] == len(DOCS)
    assert stats["question_sql"]["added"] == len(EXAMPLES)


def test_resync_is_idempotent(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = build_corpus(SCHEMA)
    store.sync_corpus(items)
    stats = store.sync_corpus(items)
    for name in ("ddl", "documentation", "question_sql"):
        assert stats[name]["added"] == 0
        assert stats[name]["deleted"] == 0


def test_sync_prunes_removed_items(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = build_corpus(SCHEMA)
    store.sync_corpus(items)
    kept = [i for i in items if i.collection != "question_sql"]
    stats = store.sync_corpus(kept)
    assert stats["question_sql"]["deleted"] == len(EXAMPLES)
    assert stats["question_sql"]["added"] == 0


def test_query_returns_relevant_example(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.sync_corpus(build_corpus(SCHEMA))
    hits = store.query("question_sql", "revenue per route", n_results=1)
    assert len(hits) == 1
    assert "sql" in hits[0].metadata


def test_query_empty_collection_is_safe(tmp_path: Path) -> None:
    assert _store(tmp_path).query("ddl", "anything") == []


@pytest.mark.integration
def test_seed_from_live_introspected_schema(tmp_path: Path) -> None:
    """The full pipeline: introspect the live DB → build corpus → seed → query."""
    try:
        schema = introspect_from_settings()
    except MySQLError as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no MySQL reachable: {exc}")

    store = _store(tmp_path)
    stats = store.sync_corpus(build_corpus(schema))
    assert stats["ddl"]["added"] == 7  # the 7 business tables
    hits = store.query("ddl", "freight revenue per route by shipment", n_results=1)
    assert hits and hits[0].metadata["table"] in {t.name for t in schema.tables}
