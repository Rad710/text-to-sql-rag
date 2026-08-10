"""Pure tests for the 4-tier retrieval merge and its helpers."""

from __future__ import annotations

from app.retrieval import (
    RetrievedContext,
    extract_tables_from_sql,
    follow_relationships,
    keyword_tables,
    merge_candidates,
)
from app.schema import Column, ForeignKey, SchemaInfo, Table


def _t(name: str, *cols: str, pk: str | None = None, fks: tuple[ForeignKey, ...] = ()) -> Table:
    columns = tuple(Column(c, "int", nullable=False, is_primary_key=(c == pk)) for c in cols)
    return Table(name=name, columns=columns, foreign_keys=fks)


DRIVER = _t("driver", "driver_code", "driver_name", pk="driver_code")
ROUTE = _t("route", "route_code", "origin", "destination", pk="route_code")
PRODUCT = _t("product", "product_code", "product_name", pk="product_code")
SHIPMENT = _t(
    "shipment",
    "shipment_code",
    "driver_code",
    "route_code",
    "product_code",
    pk="shipment_code",
    fks=(
        ForeignKey("driver_code", "driver", "driver_code"),
        ForeignKey("route_code", "route", "route_code"),
        ForeignKey("product_code", "product", "product_code"),
    ),
)
SCHEMA = SchemaInfo(tables=(DRIVER, ROUTE, PRODUCT, SHIPMENT))
KNOWN = {t.name for t in SCHEMA.tables}


def test_extract_tables_from_sql_in_order() -> None:
    sql = "SELECT * FROM shipment s JOIN driver d ON s.driver_code = d.driver_code"
    assert extract_tables_from_sql(sql, KNOWN) == ["shipment", "driver"]


def test_extract_ignores_unknown_tables_and_bad_sql() -> None:
    assert extract_tables_from_sql("SELECT * FROM some_other_table", KNOWN) == []
    assert extract_tables_from_sql("not valid sql ((", KNOWN) == []


def test_keyword_tables_matches_name_and_columns() -> None:
    assert "route" in keyword_tables("revenue per route", SCHEMA)
    # 'driver' token matches the driver table by name:
    assert "driver" in keyword_tables("which driver hauled the most", SCHEMA)


def test_follow_relationships_pulls_join_partners() -> None:
    partners = follow_relationships(["shipment"], SCHEMA)
    assert set(partners) == {"driver", "route", "product"}
    # already-chosen tables are excluded
    assert "shipment" not in follow_relationships(["shipment"], SCHEMA)


def test_merge_priority_and_tie_breaking() -> None:
    merged = merge_candidates(
        semantic=["shipment"],
        example=["driver"],
        relationship=["route"],
        keyword=["shipment", "product"],  # shipment repeats — must stay 'semantic'
    )
    assert [c.table for c in merged] == ["shipment", "driver", "route", "product"]
    by_table = {c.table: c.source for c in merged}
    assert by_table["shipment"] == "semantic"
    assert by_table["product"] == "keyword"


def test_as_prompt_has_all_sections() -> None:
    ctx = RetrievedContext(
        tables=["shipment"],
        ddl=["CREATE TABLE shipment (...)"],
        summaries=["driver(driver_code int PK)"],
        docs=["Always filter deleted = 0."],
        examples=[("total revenue", "SELECT SUM(price) FROM shipment")],
    )
    prompt = ctx.as_prompt()
    assert "-- Relevant tables" in prompt
    assert "-- Other tables" in prompt
    assert "-- Business rules" in prompt
    assert "-- Example queries" in prompt
    assert "SELECT SUM(price) FROM shipment" in prompt
