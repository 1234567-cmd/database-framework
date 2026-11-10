-- Step M1240: Rename column service_hotels.check_in to check_in_date
-- Direction: up
-- Findings: SCH-061-b7837c3b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_hotels.check_in exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hotels' AND table_schema = DATABASE() AND column_name = 'check_in'
-- Precheck: Column service_hotels.check_in_date does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hotels' AND table_schema = DATABASE() AND column_name = 'check_in_date'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hotels` RENAME COLUMN `check_in` TO `check_in_date`, ALGORITHM=INPLACE, LOCK=NONE;
