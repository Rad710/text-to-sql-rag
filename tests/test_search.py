"""Chroma-backed tests for RagStore.search_schema (temp dir; hand schema + live schema)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.corpus import build_corpus
from app.embeddings import OfflineEmbedder
from app.engine import RagStore
from app.schema import Column, ForeignKey, SchemaInfo, Table


def _t(name: str, *cols: str, pk: str, fks: tuple[ForeignKey, ...] = ()) -> Table:
    columns = tuple(Column(c, "int", nullable=False, is_primary_key=(c == pk)) for c in cols)
    return Table(name=name, columns=columns, foreign_keys=fks)


DRIVER = _t("driver", "driver_code", "driver_name", pk="driver_code")
ROUTE = _t("route", "route_code", "origin", "destination", "price", pk="route_code")
PRODUCT = _t("product", "product_code", "product_name", pk="product_code")
SHIPMENT = _t(
    "shipment",
    "shipment_code",
    "driver_code",
    "route_code",
    "product_code",
    "price",
    pk="shipment_code",
    fks=(
        ForeignKey("driver_code", "driver", "driver_code"),
        ForeignKey("route_code", "route", "route_code"),
        ForeignKey("product_code", "product", "product_code"),
    ),
)
SCHEMA = SchemaInfo(tables=(DRIVER, ROUTE, PRODUCT, SHIPMENT))


def _seeded(tmp_path: Path) -> RagStore:
    store = RagStore(path=str(tmp_path), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(SCHEMA))
    return store


def test_search_returns_relevant_context(tmp_path: Path) -> None:
    ctx = _seeded(tmp_path).search_schema("total freight revenue per route", SCHEMA)
    # shipment is named in the matching few-shot SQL → selected via the example tier.
    assert "shipment" in ctx.tables
    assert set(ctx.tables) <= {t.name for t in SCHEMA.tables}
    assert ctx.docs and ctx.examples
    prompt = ctx.as_prompt()
    assert "-- Relevant tables" in prompt and "-- Example queries" in prompt


def test_two_tier_presentation(tmp_path: Path) -> None:
    ctx = _seeded(tmp_path).search_schema("revenue per route", SCHEMA, max_full_ddl=2)
    assert len(ctx.tables) == 2  # full DDL for the top 2
    assert ctx.summaries  # the remaining tables appear as compact summaries
    # every table shows up somewhere (full DDL or summary)
    shown = len(ctx.ddl) + len(ctx.summaries)
    assert shown == len(SCHEMA.tables)


def test_relationship_following_surfaces_unnamed_table(tmp_path: Path) -> None:
    # driver is not named in the question, but shipment (chosen) joins it → it should appear.
    ctx = _seeded(tmp_path).search_schema("total freight revenue by shipment", SCHEMA)
    assert "driver" in ctx.tables


@pytest.mark.integration
def test_search_against_live_schema(tmp_path: Path) -> None:
    import pymysql

    from app.introspect import introspect_from_settings

    try:
        schema = introspect_from_settings()
    except pymysql.MySQLError as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"no MySQL reachable: {exc}")

    store = RagStore(path=str(tmp_path), embedder=OfflineEmbedder())
    store.sync_corpus(build_corpus(schema))
    ctx = store.search_schema("which drivers have unpaid settlements pending", schema)
    assert ctx.tables
    assert {"driver", "driver_payroll"} & set(ctx.tables)
    assert ctx.as_prompt()
