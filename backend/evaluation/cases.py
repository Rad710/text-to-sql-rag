"""Golden evaluation cases: a natural-language question + an independent reference (gold) SQL.

The gold SQL is written independently of the corpus examples (different structure where natural) but
must return the same result set as the correct answer — so the harness validates *semantics*, not
the SQL text.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvalCase:
    id: str
    question: str
    gold_sql: str


GOLD_CASES: tuple[EvalCase, ...] = (
    EvalCase(
        "revenue_per_route",
        "facturación total por ruta",
        # grouped by origin/destination (routes are distinct pairs) — same rows as by route_code
        "SELECT origin, destination, SUM(price) AS revenue FROM shipment WHERE deleted = 0 "
        "GROUP BY origin, destination",
    ),
    EvalCase(
        "trips_and_kilos_per_driver",
        "how many shipments did each driver make and total kilos",
        "SELECT driver_name, COUNT(*) AS trips, SUM(origin_weight) AS kg FROM shipment "
        "WHERE deleted = 0 GROUP BY driver_code, driver_name",
    ),
    EvalCase(
        "weight_loss_per_product",
        "weight loss per product",
        "SELECT product_name, SUM(origin_weight) - SUM(destination_weight) AS loss FROM shipment "
        "WHERE deleted = 0 GROUP BY product_code, product_name",
    ),
    EvalCase(
        "uncollected_planillas",
        "planillas sin cobrar y su total pendiente",
        "SELECT sp.payroll_code, SUM(s.price) AS outstanding FROM shipment_payroll sp "
        "JOIN shipment s ON s.shipment_payroll_code = sp.payroll_code "
        "WHERE sp.deleted = 0 AND s.deleted = 0 AND sp.collected = 0 GROUP BY sp.payroll_code",
    ),
    EvalCase(
        "expenses_with_without_receipt",
        "gastos de choferes con y sin recibo",
        "SELECT CASE WHEN receipt IS NULL THEN 'sin recibo' ELSE 'con recibo' END AS kind, "
        "SUM(amount) AS total FROM shipment_expense WHERE deleted = 0 GROUP BY kind",
    ),
    EvalCase(
        "top_5_routes",
        "top 5 routes by shipment count and revenue",
        "SELECT origin, destination, COUNT(*) AS trips, SUM(price) AS revenue FROM shipment "
        "WHERE deleted = 0 GROUP BY origin, destination ORDER BY trips DESC LIMIT 5",
    ),
    EvalCase(
        "monthly_revenue_this_year",
        "monthly revenue trend this year",
        "SELECT MONTH(shipment_date) AS m, SUM(price) AS revenue FROM shipment "
        "WHERE deleted = 0 AND YEAR(shipment_date) = YEAR(CURDATE()) GROUP BY MONTH(shipment_date)",
    ),
    EvalCase(
        "unpaid_settlements",
        "drivers with unpaid settlements and pending amount",
        "SELECT d.driver_name, SUM(s.payroll_price) AS pending FROM driver_payroll dp "
        "JOIN driver d ON d.driver_code = dp.driver_code "
        "JOIN shipment s ON s.driver_payroll_code = dp.payroll_code "
        "WHERE dp.deleted = 0 AND dp.paid = 0 AND s.deleted = 0 "
        "GROUP BY d.driver_code, d.driver_name",
    ),
)
