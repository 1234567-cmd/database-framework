-- Step M1245: Rename column service_miscellaneous.start_date_time to start_date_at
-- Direction: down
-- Findings: SCH-061-c5eeac1a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_miscellaneous.start_date_time exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_miscellaneous' AND table_schema = DATABASE() AND column_name = 'start_date_time'
-- Precheck: Column service_miscellaneous.start_date_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_miscellaneous' AND table_schema = DATABASE() AND column_name = 'start_date_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_miscellaneous` RENAME COLUMN `start_date_at` TO `start_date_time`, ALGORITHM=INPLACE, LOCK=NONE;
