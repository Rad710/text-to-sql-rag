-- DYR Transportes — synthetic seed data. OBVIOUSLY FAKE: placeholder names/plates/tickets, no real
-- business data or PII. Dates are relative to NOW() so "this month" / "last month" / "this year"
-- questions always return rows. Auto-applied on first MySQL boot (runs after 01_schema.sql).

USE dyrtransportes;
SET NAMES utf8mb4;  -- interpret this file's accented literals (María, Díaz, Maíz…) as UTF-8

-- Drivers (codes 1..4 by insertion order)
INSERT INTO driver (driver_id, driver_name, driver_surname, truck_plate, trailer_plate, modification_user) VALUES
  ('DEMO-0001', 'Juan',   'Pérez', 'TRK-001', 'TRL-001', 'seed'),
  ('DEMO-0002', 'María',  'Gómez', 'TRK-002', 'TRL-002', 'seed'),
  ('DEMO-0003', 'Carlos', 'Díaz',  'TRK-003', NULL,      'seed'),
  ('DEMO-0004', 'Ana',    'López', 'TRK-004', 'TRL-004', 'seed');

-- Routes (codes 1..4)
INSERT INTO route (origin, destination, price, payroll_price, modification_user) VALUES
  ('Asuncion',        'Ciudad del Este', 1500000.00, 1000000.00, 'seed'),
  ('Encarnacion',     'Asuncion',        1200000.00,  800000.00, 'seed'),
  ('Ciudad del Este', 'Asuncion',        1600000.00, 1100000.00, 'seed'),
  ('Asuncion',        'Encarnacion',     1250000.00,  850000.00, 'seed');

-- Products (codes 1..3)
INSERT INTO product (product_name, modification_user) VALUES
  ('Soja', 'seed'), ('Maiz', 'seed'), ('Trigo', 'seed');

-- Shipment payrolls / Planillas (codes 1..3): one collected, two outstanding
INSERT INTO shipment_payroll (payroll_timestamp, collected, collection_timestamp, modification_user) VALUES
  (NOW() - INTERVAL 3 DAY,  1, NOW() - INTERVAL 1 DAY, 'seed'),
  (NOW() - INTERVAL 40 DAY, 0, NULL,                   'seed'),
  (NOW() - INTERVAL 75 DAY, 0, NULL,                   'seed');

-- Driver payrolls / Liquidaciones (codes 1..4, one per driver): two paid, two pending
INSERT INTO driver_payroll (payroll_timestamp, driver_code, paid, paid_timestamp, modification_user) VALUES
  (NOW() - INTERVAL 3 DAY,  1, 1, NOW() - INTERVAL 1 DAY, 'seed'),
  (NOW() - INTERVAL 40 DAY, 2, 0, NULL,                   'seed'),
  (NOW() - INTERVAL 40 DAY, 3, 0, NULL,                   'seed'),
  (NOW() - INTERVAL 75 DAY, 4, 1, NOW() - INTERVAL 2 DAY, 'seed');

-- Shipments / Cobranzas (central fact table). Spread across ~3 months; denormalized fields kept
-- consistent with the referenced driver/route/product rows.
INSERT INTO shipment
  (shipment_date, driver_name, truck_plate, trailer_plate, driver_code, product_code, product_name,
   route_code, origin, destination, price, payroll_price, dispatch_code, receipt_code,
   origin_weight, destination_weight, shipment_payroll_code, driver_payroll_code, modification_user)
VALUES
  (NOW() - INTERVAL 2 DAY,  'Juan',   'TRK-001', 'TRL-001', 1, 1, 'Soja',  1, 'Asuncion',        'Ciudad del Este', 1500000.00, 1000000.00, 'D1001', 'R2001', 42000, 41850, 1, 1, 'seed'),
  (NOW() - INTERVAL 5 DAY,  'Juan',   'TRK-001', 'TRL-001', 1, 2, 'Maiz',  3, 'Ciudad del Este', 'Asuncion',        1600000.00, 1100000.00, 'D1002', 'R2002', 38000, 37900, 1, 1, 'seed'),
  (NOW() - INTERVAL 8 DAY,  'María',  'TRK-002', 'TRL-002', 2, 1, 'Soja',  2, 'Encarnacion',     'Asuncion',        1200000.00,  800000.00, 'D1003', 'R2003', 40000, 39800, 1, 2, 'seed'),
  (NOW() - INTERVAL 12 DAY, 'María',  'TRK-002', 'TRL-002', 2, 3, 'Trigo', 4, 'Asuncion',        'Encarnacion',     1250000.00,  850000.00, 'D1004', 'R2004', 35000, 34950, 2, 2, 'seed'),
  (NOW() - INTERVAL 3 DAY,  'Carlos', 'TRK-003', NULL,      3, 2, 'Maiz',  1, 'Asuncion',        'Ciudad del Este', 1500000.00, 1000000.00, 'D1005', 'R2005', 44000, 43800, 2, 3, 'seed'),
  (NOW() - INTERVAL 15 DAY, 'Carlos', 'TRK-003', NULL,      3, 1, 'Soja',  3, 'Ciudad del Este', 'Asuncion',        1600000.00, 1100000.00, 'D1006', 'R2006', 41000, 40850, 2, 3, 'seed'),
  (NOW() - INTERVAL 6 DAY,  'Ana',    'TRK-004', 'TRL-004', 4, 3, 'Trigo', 2, 'Encarnacion',     'Asuncion',        1200000.00,  800000.00, 'D1007', 'R2007', 33000, 32900, 3, 4, 'seed'),
  (NOW() - INTERVAL 20 DAY, 'Ana',    'TRK-004', 'TRL-004', 4, 1, 'Soja',  4, 'Asuncion',        'Encarnacion',     1250000.00,  850000.00, 'D1008', 'R2008', 45000, 44700, 3, 4, 'seed'),
  (NOW() - INTERVAL 35 DAY, 'Juan',   'TRK-001', 'TRL-001', 1, 1, 'Soja',  1, 'Asuncion',        'Ciudad del Este', 1500000.00, 1000000.00, 'D1009', 'R2009', 42500, 42350, 1, 1, 'seed'),
  (NOW() - INTERVAL 40 DAY, 'María',  'TRK-002', 'TRL-002', 2, 2, 'Maiz',  2, 'Encarnacion',     'Asuncion',        1200000.00,  800000.00, 'D1010', 'R2010', 39000, 38850, 2, 2, 'seed'),
  (NOW() - INTERVAL 45 DAY, 'Carlos', 'TRK-003', NULL,      3, 3, 'Trigo', 3, 'Ciudad del Este', 'Asuncion',        1600000.00, 1100000.00, 'D1011', 'R2011', 36000, 35900, 2, 3, 'seed'),
  (NOW() - INTERVAL 50 DAY, 'Ana',    'TRK-004', 'TRL-004', 4, 2, 'Maiz',  4, 'Asuncion',        'Encarnacion',     1250000.00,  850000.00, 'D1012', 'R2012', 37500, 37400, 3, 4, 'seed'),
  (NOW() - INTERVAL 65 DAY, 'Juan',   'TRK-001', 'TRL-001', 1, 1, 'Soja',  3, 'Ciudad del Este', 'Asuncion',        1600000.00, 1100000.00, 'D1013', 'R2013', 43000, 42800, 1, 1, 'seed'),
  (NOW() - INTERVAL 72 DAY, 'María',  'TRK-002', 'TRL-002', 2, 3, 'Trigo', 1, 'Asuncion',        'Ciudad del Este', 1500000.00, 1000000.00, 'D1014', 'R2014', 34000, 33950, 2, 2, 'seed'),
  (NOW() - INTERVAL 80 DAY, 'Carlos', 'TRK-003', NULL,      3, 1, 'Soja',  2, 'Encarnacion',     'Asuncion',        1200000.00,  800000.00, 'D1015', 'R2015', 40500, 40300, 3, 3, 'seed'),
  (NOW() - INTERVAL 88 DAY, 'Ana',    'TRK-004', 'TRL-004', 4, 2, 'Maiz',  3, 'Ciudad del Este', 'Asuncion',        1600000.00, 1100000.00, 'D1016', 'R2016', 38500, 38400, 3, 4, 'seed');

-- Shipment expenses / Liquidacion Gastos: some with receipt, some without (receipt NULL)
INSERT INTO shipment_expense (expense_date, receipt, amount, reason, driver_payroll_code, modification_user) VALUES
  (NOW() - INTERVAL 3 DAY,  'F-9001', 500000, 'Combustible', 1, 'seed'),
  (NOW() - INTERVAL 4 DAY,  NULL,     150000, 'Peaje',       1, 'seed'),
  (NOW() - INTERVAL 9 DAY,  'F-9002', 620000, 'Combustible', 2, 'seed'),
  (NOW() - INTERVAL 10 DAY, NULL,      90000, 'Viaticos',    2, 'seed'),
  (NOW() - INTERVAL 14 DAY, 'F-9003', 480000, 'Combustible', 3, 'seed'),
  (NOW() - INTERVAL 18 DAY, 'F-9004', 300000, 'Reparacion',  4, 'seed'),
  (NOW() - INTERVAL 21 DAY, NULL,     120000, 'Peaje',       4, 'seed');
