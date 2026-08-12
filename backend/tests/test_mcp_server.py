"""Tests for the standalone read-only SQL MCP server (task 0011).

The two tools are thin adapters over the existing RAG + safety layers, so these tests check the
wiring (and that run_sql surfaces safety rejections as text) without a live MCP client or DB.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

import app.mcp_server as mcp_server
from app.rag.corpus import build_corpus
from app.rag.embeddings import OfflineEmbedder
from app.rag.engine import RagStore
from app.rag.schema import Column, ForeignKey, SchemaInfo, Table
from app.safety.execution import RunResult


def _t(name: str, *cols: str, pk: str, fks: tuple[ForeignKey, ...] = ()) -> Table:
    columns = tuple(Column(c, "int", nullable=False, is_primary_key=(c == pk)) for c in cols)
    return Table(name=name, columns=columns, foreign_keys=fks)


DRIVER = _t("driver", "driver_code", "driver_name", pk="driver_code")
SHIPMENT = _t(
    "shipment",
    "shipment_code",
    "driver_code",
    "price",
    pk="shipment_code",
    fks=(ForeignKey("driver_code", "driver", "driver_code"),),
)
SCHEMA = SchemaInfo(tables=(DRIVER, SHIPMENT))


def test_run_sql_tool_formats_rows_as_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "_run_sql",
        lambda q: RunResult(sql=q, columns=["revenue"], rows=[("8000000",)]),
    )
    out = mcp_server.run_sql("SELECT SUM(price) AS revenue FROM shipment")
    assert "| revenue |" in out
    assert "8000000" in out
    assert "(1 rows)" in out


def test_run_sql_tool_surfaces_safety_rejection(monkeypatch: pytest.MonkeyPatch) -> None:
    # A blocked query returns a structured error from run_sql; the tool emits it as text.
    monkeypatch.setattr(
        mcp_server,
        "_run_sql",
        lambda q: RunResult(sql=q, error="rejected: only read-only SELECT statements are allowed"),
    )
    out = mcp_server.run_sql("DELETE FROM shipment")
    assert out.startswith("ERROR:")
    assert "read-only" in out


def test_search_schema_tool_returns_retrieved_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = RagStore(path=str(tmp_path), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(SCHEMA))
    monkeypatch.setattr(mcp_server, "get_service", lambda: (store, SCHEMA))

    out = mcp_server.search_schema("total revenue per driver")
    assert isinstance(out, str) and out
    assert "shipment" in out  # the relevant table's DDL is in the retrieved context


def test_both_tools_are_registered() -> None:
    tools = asyncio.run(mcp_server.server.list_tools())
    assert {t.name for t in tools} == {"search_schema", "run_sql"}
