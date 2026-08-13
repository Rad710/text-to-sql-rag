# Reference — schema & constants

The **single source of truth** for the demo database shape and fixed facts. Tasks and docs link here;
they never restate it. The DB is **synthetic** — this describes the *shape*, seeded with obviously-fake
data (task 0002).

## Domain

**DYR Transportes** is a freight/trucking business in Paraguay (currency Guaraníes, "Gs."; reports to
DINATRAN, the national transport regulator). It hauls bulk product by truck along fixed origin→destination
**routes**, tracking each **shipment** (weighed at origin and destination). Two money flows: billing
**clients** for freight (grouped into shipment payrolls / *planillas*, marked collected) and paying
**drivers** for their trips minus expenses (grouped into driver payrolls / *liquidaciones*).

Spanish domain terms: *Cobranzas* = shipments/collections · *Nómina* = drivers · *Precios* = routes/prices
· *Planillas* = shipment payrolls · *Liquidaciones* = driver settlements · *Fletes* = freight fees.

## Scope of the synthetic demo

The demo materializes **only the 7 business tables** below (via `mock-db/migration/*`, see
[decisions/0011](decisions/0011-flyway-mock-db-migrations.md)). The real project's `*_audit` companion
tables + triggers and the `user` auth table are **omitted** as query-irrelevant noise.

## Engine

**MySQL 8** (real project uses MySQL 9 via SQLAlchemy 2.0 + Alembic). Money = `DECIMAL(10,2)`; weights =
`DECIMAL(10,0)`; expense amount = `DECIMAL(20,0)`. Every business table carries `deleted BOOL` (soft
delete — **always filter `deleted = 0`**), `modification_user VARCHAR(100)`, `modification_timestamp
TIMESTAMP`, and mirrors into a `*_audit` companion table (identical columns + an `audit_code` PK).

## Tables

### `driver` — *Nómina*
`driver_code` INT PK (autoinc) · `driver_id` VARCHAR(100) national ID · `driver_name` VARCHAR(100) ·
`driver_surname` VARCHAR(100) null · `truck_plate` VARCHAR(100) · `trailer_plate` VARCHAR(100) null ·
(+ soft-delete/audit columns). → 1:N `shipment`, `driver_payroll`.

### `route` — *Precios*
`route_code` INT PK · `origin` VARCHAR(100) · `destination` VARCHAR(100) · `price` DECIMAL(10,2) charged
to client · `payroll_price` DECIMAL(10,2) paid to driver. → 1:N `shipment`.

### `product` — *Productos*
`product_code` INT PK · `product_name` VARCHAR(100). → 1:N `shipment`.

### `shipment_payroll` — *Planillas* (client billing batch)
`payroll_code` INT PK · `payroll_timestamp` TIMESTAMP · `collected` BOOL · `collection_timestamp`
TIMESTAMP null. → 1:N `shipment`.

### `driver_payroll` — *Liquidaciones* (driver settlement batch)
`payroll_code` INT PK · `payroll_timestamp` TIMESTAMP · `driver_code` INT **FK→driver** · `paid` BOOL ·
`paid_timestamp` TIMESTAMP null. → 1:N `shipment`, `shipment_expense`.

### `shipment` — *Cobranzas* (central fact table)
`shipment_code` INT PK · `shipment_date` TIMESTAMP · `driver_code` INT **FK→driver** · `product_code` INT
**FK→product** · `route_code` INT **FK→route** · `shipment_payroll_code` INT **FK→shipment_payroll** ·
`driver_payroll_code` INT **FK→driver_payroll** · `price` DECIMAL(10,2) client freight fee ·
`payroll_price` DECIMAL(10,2) driver pay · `dispatch_code` / `receipt_code` VARCHAR(100) tickets ·
`origin_weight` / `destination_weight` DECIMAL(10,0) kg · **denormalized snapshots**: `driver_name`,
`product_name`, `origin`, `destination`, `price`, `payroll_price`.
Unique `(driver_code, dispatch_code, receipt_code, shipment_date, route_code, product_code)`. This is the
join hub. *Note:* many questions can be answered from `shipment` alone thanks to the denormalized columns.

### `shipment_expense` — *Liquidación Gastos* (driver expenses)
`expense_code` INT PK · `expense_date` TIMESTAMP · `receipt` VARCHAR(100) null (null ⇒ "without receipt")
· `amount` DECIMAL(20,0) Gs. · `reason` VARCHAR(100) null · `driver_payroll_code` INT **FK→driver_payroll**.

### `user` — auth only (isolated; no FK to business tables)
`user_id` VARCHAR(36) UUID PK · `email` unique · `name` · `password_hash`.

## Relationship map
```
driver ──1:N── shipment ──N:1── route
   │              │  └──N:1── product
   │              ├──N:1── shipment_payroll   (client billing batch)
   │              └──N:1── driver_payroll     (driver settlement batch)
   └──1:N── driver_payroll ──1:N── shipment_expense
```

## Canonical demo questions (NL → what it exercises)

1. Total freight revenue (`SUM(price)`) per route between two dates.
2. Shipments per driver last month + total kilos (`SUM(origin_weight)`).
3. Weight loss per product (`SUM(origin_weight - destination_weight)`).
4. Amount owed per driver = `SUM(payroll_price)` − `SUM(expense.amount)` via `driver_payroll`.
5. Uncollected *planillas* (`collected = 0`) and their outstanding total.
6. Driver expenses split by with-receipt vs without (`receipt IS NULL`).
7. Top 5 routes by shipment count and revenue.
8. Monthly revenue trend for the current year.
9. Total kilos + freight per truck plate (DINATRAN-style report).
10. Drivers with unpaid settlements (`paid = 0`) and pending amount.

## Constants (to be pinned as code lands)
- Default result cap: `LIMIT 500` (enforced in code — see [decisions/0003](decisions/0003-sql-safety-defense-in-depth.md)).
- Agent loop cap: max tool-call iterations (set in task 0008).
- Always filter `deleted = 0` on business tables.
