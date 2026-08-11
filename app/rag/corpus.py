"""The RAG corpus: what the retriever indexes.

Three kinds of item, each with a content-derived id so seeding is idempotent (unchanged content
keeps its id and is skipped; changed content becomes a new id and the old one is pruned):

* **ddl** — the annotated ``CREATE TABLE`` per table (from live introspection, :mod:`app.schema`).
* **documentation** — hand-written business-rule notes.
* **question_sql** — curated NL→SQL pairs; the *question* is embedded, the SQL rides in metadata.

`build_corpus` is pure given a ``SchemaInfo``. A test keeps every EXAMPLE SQL passing the validator.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.rag.schema import SchemaInfo, render_table_ddl, render_table_summary

COLLECTIONS = ("ddl", "documentation", "question_sql")


@dataclass(frozen=True, slots=True)
class CorpusItem:
    collection: str
    text: str  # the text that gets embedded
    metadata: dict[str, str]

    @property
    def id(self) -> str:
        digest = hashlib.sha256(f"{self.collection}\n{self.text}".encode())
        return digest.hexdigest()[:16]


# --- Business-rule documentation (topic, note) -------------------------------------------------
DOCS: tuple[tuple[str, str], ...] = (
    (
        "soft-delete",
        "Every business table has a `deleted` flag. Only rows with `deleted = 0` are active — "
        "always filter `WHERE deleted = 0`.",
    ),
    (
        "shipment-denormalized",
        "The `shipment` table denormalizes `driver_name`, `product_name`, `origin`, `destination`, "
        "`price` and `payroll_price`, so many questions need no joins — `shipment` alone suffices.",
    ),
    (
        "money",
        "Money is in Paraguayan Guaraníes (Gs.). `shipment.price` is the freight fee charged "
        "to the client (revenue); `shipment.payroll_price` is what the driver is paid.",
    ),
    (
        "weights",
        "`origin_weight` and `destination_weight` are kilograms. Weight loss in transit = "
        "`origin_weight - destination_weight`.",
    ),
    (
        "billing-planillas",
        "A `shipment_payroll` (planilla) groups shipments billed to a client; `collected = 1` "
        "means paid. Uncollected billing is `collected = 0`.",
    ),
    (
        "settlement-liquidaciones",
        "A `driver_payroll` (liquidación) groups a driver's trips; `paid = 1` means the driver was "
        "paid. Driver expenses are in `shipment_expense`, where `receipt IS NULL` means "
        "no receipt.",
    ),
    (
        "dates",
        "`shipment_date` and `expense_date` are timestamps; use them for time filters (this month, "
        "last month, per month, per year).",
    ),
)

# --- Curated NL→SQL few-shots. Bilingual (EN + ES): each SQL is reachable by a question in either
# language, so retrieval and the mock work for both. Every SQL must pass validate_read_only.
_EXAMPLE_SPECS: tuple[tuple[str, str, str], ...] = (
    (
        "total freight revenue per route",
        "facturación total por ruta",
        "SELECT origin, destination, SUM(price) AS revenue FROM shipment WHERE deleted = 0 "
        "GROUP BY route_code, origin, destination ORDER BY revenue DESC",
    ),
    (
        "how many shipments did each driver make and total kilos",
        "cuántos viajes hizo cada chofer y cuántos kilos",
        "SELECT driver_name, COUNT(*) AS trips, SUM(origin_weight) AS total_kg FROM shipment "
        "WHERE deleted = 0 GROUP BY driver_code, driver_name ORDER BY trips DESC",
    ),
    (
        "weight loss per product",
        "pérdida de peso por producto",
        "SELECT product_name, SUM(origin_weight - destination_weight) AS weight_loss_kg "
        "FROM shipment WHERE deleted = 0 GROUP BY product_code, product_name "
        "ORDER BY weight_loss_kg DESC",
    ),
    (
        "which shipment payrolls are uncollected and their outstanding total",
        "planillas sin cobrar y su total pendiente",
        "SELECT sp.payroll_code, SUM(s.price) AS outstanding FROM shipment_payroll sp "
        "JOIN shipment s ON s.shipment_payroll_code = sp.payroll_code "
        "WHERE sp.deleted = 0 AND s.deleted = 0 AND sp.collected = 0 GROUP BY sp.payroll_code",
    ),
    (
        "driver expenses split by with-receipt vs without",
        "gastos de choferes con y sin recibo",
        "SELECT CASE WHEN receipt IS NULL THEN 'sin recibo' ELSE 'con recibo' END AS kind, "
        "SUM(amount) AS total FROM shipment_expense WHERE deleted = 0 GROUP BY kind",
    ),
    (
        "top 5 routes by shipment count and revenue",
        "top 5 rutas por cantidad de viajes e ingresos",
        "SELECT origin, destination, COUNT(*) AS trips, SUM(price) AS revenue FROM shipment "
        "WHERE deleted = 0 GROUP BY route_code, origin, destination ORDER BY trips DESC LIMIT 5",
    ),
    (
        "monthly revenue trend this year",
        "tendencia de facturación mensual este año",
        "SELECT MONTH(shipment_date) AS month, SUM(price) AS revenue FROM shipment "
        "WHERE deleted = 0 AND YEAR(shipment_date) = YEAR(CURDATE()) "
        "GROUP BY MONTH(shipment_date) ORDER BY month",
    ),
    (
        "drivers with unpaid settlements and pending amount",
        "choferes con liquidaciones impagas y monto pendiente",
        "SELECT d.driver_name, SUM(s.payroll_price) AS pending FROM driver_payroll dp "
        "JOIN driver d ON d.driver_code = dp.driver_code "
        "JOIN shipment s ON s.driver_payroll_code = dp.payroll_code "
        "WHERE dp.deleted = 0 AND dp.paid = 0 AND s.deleted = 0 "
        "GROUP BY d.driver_code, d.driver_name",
    ),
)

# Flatten to (question, sql) pairs — one per language.
EXAMPLES: tuple[tuple[str, str], ...] = tuple(
    (question, sql) for en, es, sql in _EXAMPLE_SPECS for question in (en, es)
)


def build_corpus(schema: SchemaInfo) -> list[CorpusItem]:
    """Combine the introspected DDL with the static docs + examples into corpus items."""
    items: list[CorpusItem] = []
    for table in schema.tables:
        items.append(
            CorpusItem(
                collection="ddl",
                text=render_table_ddl(schema, table),
                metadata={"table": table.name, "summary": render_table_summary(table)},
            )
        )
    for topic, note in DOCS:
        items.append(CorpusItem(collection="documentation", text=note, metadata={"topic": topic}))
    for question, sql in EXAMPLES:
        items.append(CorpusItem(collection="question_sql", text=question, metadata={"sql": sql}))
    return items
