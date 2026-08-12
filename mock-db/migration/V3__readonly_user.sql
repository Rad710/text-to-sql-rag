-- Create the SELECT-only application user — the real read-only guarantee (decision 0003).
-- The password is injected by Flyway from the ${db_password} placeholder (env
-- FLYWAY_PLACEHOLDERS_DB_PASSWORD), so no credential is hardcoded here. Replaces the former
-- 03_grant_readonly.sh; runs as the last mock-db migration (decision 0011 supersedes 0004).
CREATE USER IF NOT EXISTS 'llm_readonly'@'%' IDENTIFIED BY '${db_password}';
-- SELECT only, on the demo schema only. No INSERT/UPDATE/DELETE/DDL, no other databases.
GRANT SELECT ON `dyrtransportes`.* TO 'llm_readonly'@'%';
FLUSH PRIVILEGES;
