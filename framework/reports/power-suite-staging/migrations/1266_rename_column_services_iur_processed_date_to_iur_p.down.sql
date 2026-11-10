-- Step M1266: Rename column services.iur_processed_date to iur_processed_at
-- Direction: down
-- Findings: SCH-061-a6a2c526
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column services.iur_processed_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'services' AND table_schema = DATABASE() AND column_name = 'iur_processed_date'
-- Precheck: Column services.iur_processed_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'services' AND table_schema = DATABASE() AND column_name = 'iur_processed_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `services` RENAME COLUMN `iur_processed_at` TO `iur_processed_date`, ALGORITHM=INPLACE, LOCK=NONE;
