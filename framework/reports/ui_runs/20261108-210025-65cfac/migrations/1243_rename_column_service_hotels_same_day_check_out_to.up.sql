-- Step M1243: Rename column service_hotels.same_day_check_out to is_same_day_check_out
-- Direction: up
-- Findings: SCH-060-239e1fd1
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_hotels.same_day_check_out exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hotels' AND table_schema = DATABASE() AND column_name = 'same_day_check_out'
-- Precheck: Column service_hotels.is_same_day_check_out does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hotels' AND table_schema = DATABASE() AND column_name = 'is_same_day_check_out'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hotels` RENAME COLUMN `same_day_check_out` TO `is_same_day_check_out`, ALGORITHM=INPLACE, LOCK=NONE;
