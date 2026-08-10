"""Pure tests for the RAG corpus builder + the EXAMPLE-SQL validity invariant."""

from __future__ import annotations

from app.corpus import COLLECTIONS, DOCS, EXAMPLES, build_corpus
from app.schema import Column, ForeignKey, SchemaInfo, Table
from app.validator import validate_read_only

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


def test_build_corpus_counts_by_collection() -> None:
    items = build_corpus(SCHEMA)
    by = {c: [i for i in items if i.collection == c] for c in COLLECTIONS}
    assert len(by["ddl"]) == 2  # one per table
    assert len(by["documentation"]) == len(DOCS)
    assert len(by["question_sql"]) == len(EXAMPLES)


def test_ids_are_stable_content_hashes() -> None:
    ids1 = [i.id for i in build_corpus(SCHEMA)]
    ids2 = [i.id for i in build_corpus(SCHEMA)]
    assert ids1 == ids2
    assert all(len(i) == 16 for i in ids1)
    assert len(set(ids1)) == len(ids1)  # no collisions


def test_ddl_items_carry_table_and_summary_metadata() -> None:
    items = build_corpus(SCHEMA)
    ddl = next(i for i in items if i.collection == "ddl" and i.metadata["table"] == "shipment")
    assert "-- joins: driver" in ddl.text
    assert ddl.metadata["summary"].startswith("shipment(")


def test_every_example_sql_is_valid_read_only() -> None:
    # cross-module invariant: the curated few-shot SQL must pass the safety validator.
    for _question, sql in EXAMPLES:
        validate_read_only(sql)  # raises ValidationError on failure
