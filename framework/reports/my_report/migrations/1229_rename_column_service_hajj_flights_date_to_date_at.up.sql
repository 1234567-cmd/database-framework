-- Step M1229: Rename column service_hajj_flights.date to date_at
-- Direction: up
-- Findings: SCH-061-6385d9d6
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_hajj_flights.date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajj_flights' AND table_schema = DATABASE() AND column_name = 'date'
-- Precheck: Column service_hajj_flights.date_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajj_flights' AND table_schema = DATABASE() AND column_name = 'date_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hajj_flights` RENAME COLUMN `date` TO `date_at`, ALGORITHM=INPLACE, LOCK=NONE;
