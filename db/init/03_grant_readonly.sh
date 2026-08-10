#!/usr/bin/env bash
# Create the SELECT-only application user — the real read-only guarantee (decision 0003).
# Credentials come from the ENVIRONMENT, never hardcoded. Runs last on first MySQL boot
# (/docker-entrypoint-initdb.d); also runnable standalone in CI (set MYSQL_HOST=127.0.0.1).
set -euo pipefail

: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD must be set}"
: "${DB_PASSWORD:?DB_PASSWORD must be set (password for the read-only app user)}"
DB_USER="${DB_USER:-llm_readonly}"
MYSQL_DATABASE="${MYSQL_DATABASE:-dyrtransportes}"
MYSQL_HOST="${MYSQL_HOST:-localhost}"   # localhost => container socket; 127.0.0.1 => TCP (CI)

mysql -h "${MYSQL_HOST}" -u root -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
-- SELECT only, on the demo schema only. No INSERT/UPDATE/DELETE/DDL, no other databases.
GRANT SELECT ON \`${MYSQL_DATABASE}\`.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
SQL

echo "grant: created read-only user '${DB_USER}' on '${MYSQL_DATABASE}'"
