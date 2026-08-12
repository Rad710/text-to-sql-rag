-- DYR Transportes — synthetic demo schema (read-only query target).
-- Faithful to the real dyrtransportes_flask SQLAlchemy models; business tables only
-- (audit tables + triggers + the user auth table are intentionally omitted — decision 0004).
-- Auto-applied on first MySQL boot via /docker-entrypoint-initdb.d.

USE dyrtransportes;
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

-- Drivers (Nomina)
CREATE TABLE driver (
    driver_code            INT AUTO_INCREMENT PRIMARY KEY,
    driver_id              VARCHAR(100) NOT NULL,          -- national ID
    driver_name            VARCHAR(100) NOT NULL,
    driver_surname         VARCHAR(100) NULL,
    truck_plate            VARCHAR(100) NOT NULL,
    trailer_plate          VARCHAR(100) NULL,
    deleted                BOOLEAN      NOT NULL DEFAULT 0,
    modification_user      VARCHAR(100) NOT NULL,
    modification_timestamp TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Routes (Precios): origin -> destination, price charged vs price paid to driver
CREATE TABLE route (
    route_code             INT AUTO_INCREMENT PRIMARY KEY,
    origin                 VARCHAR(100)  NOT NULL,
    destination            VARCHAR(100)  NOT NULL,
    price                  DECIMAL(10,2) NOT NULL,          -- charged to client
    payroll_price          DECIMAL(10,2) NOT NULL,          -- paid to driver
    deleted                BOOLEAN       NOT NULL DEFAULT 0,
    modification_user      VARCHAR(100)  NOT NULL,
    modification_timestamp TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Products (Productos)
CREATE TABLE product (
    product_code           INT AUTO_INCREMENT PRIMARY KEY,
    product_name           VARCHAR(100) NOT NULL,
    deleted                BOOLEAN      NOT NULL DEFAULT 0,
    modification_user      VARCHAR(100) NOT NULL,
    modification_timestamp TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Shipment payrolls (Planillas): client billing batch
CREATE TABLE shipment_payroll (
    payroll_code           INT AUTO_INCREMENT PRIMARY KEY,
    payroll_timestamp      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    collected              BOOLEAN      NOT NULL DEFAULT 0,
    collection_timestamp   TIMESTAMP    NULL     DEFAULT NULL,
    deleted                BOOLEAN      NOT NULL DEFAULT 0,
    modification_user      VARCHAR(100) NOT NULL,
    modification_timestamp TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Driver payrolls (Liquidaciones): driver settlement batch
CREATE TABLE driver_payroll (
    payroll_code           INT AUTO_INCREMENT PRIMARY KEY,
    payroll_timestamp      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    driver_code            INT          NOT NULL,
    paid                   BOOLEAN      NOT NULL DEFAULT 0,
    paid_timestamp         TIMESTAMP    NULL     DEFAULT NULL,
    deleted                BOOLEAN      NOT NULL DEFAULT 0,
    modification_user      VARCHAR(100) NOT NULL,
    modification_timestamp TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_driver_payroll_driver
        FOREIGN KEY (driver_code) REFERENCES driver (driver_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Shipments (Cobranzas): the central fact table. Denormalizes driver/product/route/price snapshots.
CREATE TABLE shipment (
    shipment_code          INT AUTO_INCREMENT PRIMARY KEY,
    shipment_date          TIMESTAMP     NOT NULL,
    driver_name            VARCHAR(100)  NOT NULL,           -- denormalized snapshot
    truck_plate            VARCHAR(100)  NOT NULL,
    trailer_plate          VARCHAR(100)  NULL,
    driver_code            INT           NOT NULL,
    product_code           INT           NOT NULL,
    product_name           VARCHAR(100)  NOT NULL,           -- denormalized
    route_code             INT           NOT NULL,
    origin                 VARCHAR(100)  NOT NULL,           -- denormalized
    destination            VARCHAR(100)  NOT NULL,           -- denormalized
    price                  DECIMAL(10,2) NOT NULL DEFAULT 0, -- client freight fee
    payroll_price          DECIMAL(10,2) NOT NULL DEFAULT 0, -- driver pay
    dispatch_code          VARCHAR(100)  NOT NULL,           -- dispatch ticket
    receipt_code           VARCHAR(100)  NOT NULL,           -- receipt ticket
    origin_weight          DECIMAL(10,0) NOT NULL,           -- kg loaded
    destination_weight     DECIMAL(10,0) NOT NULL,           -- kg delivered
    shipment_payroll_code  INT           NOT NULL,
    driver_payroll_code    INT           NOT NULL,
    deleted                BOOLEAN       NOT NULL DEFAULT 0,
    modification_user      VARCHAR(100)  NOT NULL,
    modification_timestamp TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_shipment_driver
        FOREIGN KEY (driver_code) REFERENCES driver (driver_code),
    CONSTRAINT fk_shipment_product
        FOREIGN KEY (product_code) REFERENCES product (product_code),
    CONSTRAINT fk_shipment_route
        FOREIGN KEY (route_code) REFERENCES route (route_code),
    CONSTRAINT fk_shipment_shipment_payroll
        FOREIGN KEY (shipment_payroll_code) REFERENCES shipment_payroll (payroll_code),
    CONSTRAINT fk_shipment_driver_payroll
        FOREIGN KEY (driver_payroll_code) REFERENCES driver_payroll (payroll_code),
    CONSTRAINT unique_driver_ticket_date
        UNIQUE (driver_code, dispatch_code, receipt_code, shipment_date, route_code, product_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Shipment expenses (Liquidacion Gastos): driver expenses within a settlement batch
CREATE TABLE shipment_expense (
    expense_code           INT AUTO_INCREMENT PRIMARY KEY,
    expense_date           TIMESTAMP     NOT NULL,
    receipt                VARCHAR(100)  NULL,               -- NULL => "without receipt"
    amount                 DECIMAL(20,0) NOT NULL,           -- Gs.
    reason                 VARCHAR(100)  NULL,
    driver_payroll_code    INT           NOT NULL,
    deleted                BOOLEAN       NOT NULL DEFAULT 0,
    modification_user      VARCHAR(100)  NOT NULL,
    modification_timestamp TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_expense_driver_payroll
        FOREIGN KEY (driver_payroll_code) REFERENCES driver_payroll (payroll_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Helpful indexes for the common query shapes (date filters, per-entity aggregates).
CREATE INDEX idx_shipment_date  ON shipment (shipment_date);
CREATE INDEX idx_shipment_route ON shipment (route_code);
CREATE INDEX idx_shipment_driver ON shipment (driver_code);
CREATE INDEX idx_expense_payroll ON shipment_expense (driver_payroll_code);

SET FOREIGN_KEY_CHECKS = 1;
