"""Pure tests for the schema model + DDL/annotation renderers (no database)."""

from __future__ import annotations

from app.rag.schema import (
    Column,
    ForeignKey,
    SchemaInfo,
    Table,
    render_table_ddl,
    render_table_summary,
)

DRIVER = Table(
    name="driver",
    columns=(
        Column("driver_code", "int", nullable=False, is_primary_key=True),
        Column("driver_name", "varchar(100)", nullable=False),
    ),
)

SHIPMENT = Table(
    name="shipment",
    columns=(
        Column("shipment_code", "int", nullable=False, is_primary_key=True),
        Column("driver_code", "int", nullable=False),
        Column("trailer_plate", "varchar(100)", nullable=True),
    ),
    foreign_keys=(ForeignKey("driver_code", "driver", "driver_code"),),
)

SCHEMA = SchemaInfo(tables=(DRIVER, SHIPMENT))


def test_join_annotations_are_bidirectional() -> None:
    # shipment references driver; driver is referenced by shipment — both should see each other.
    assert SCHEMA.join_partners("shipment") == ("driver",)
    assert SCHEMA.join_partners("driver") == ("shipment",)


def test_referencing_tables() -> None:
    assert SCHEMA.referencing_tables("driver") == ("shipment",)
    assert SCHEMA.referencing_tables("shipment") == ()


def test_render_ddl_shape() -> None:
    ddl = render_table_ddl(SCHEMA, SHIPMENT)
    assert ddl.startswith("-- joins: driver")
    assert "CREATE TABLE shipment (" in ddl
    assert "shipment_code int NOT NULL" in ddl
    assert "trailer_plate varchar(100)" in ddl  # nullable → no NOT NULL
    assert "trailer_plate varchar(100) NOT NULL" not in ddl
    assert "PRIMARY KEY (shipment_code)" in ddl
    assert "FOREIGN KEY (driver_code) REFERENCES driver(driver_code)" in ddl
    assert ddl.rstrip().endswith(");")


def test_render_summary_annotates_pk_and_fk() -> None:
    summary = render_table_summary(SHIPMENT)
    assert summary.startswith("shipment(")
    assert "shipment_code int PK" in summary
    assert "driver_code int ->driver" in summary


def test_summary_truncates_wide_tables() -> None:
    wide = Table(
        name="wide",
        columns=tuple(Column(f"c{i}", "int", nullable=True) for i in range(20)),
    )
    summary = render_table_summary(wide, max_cols=5)
    assert "c0 int" in summary
    assert "c19" not in summary
    assert "(+15 more)" in summary
