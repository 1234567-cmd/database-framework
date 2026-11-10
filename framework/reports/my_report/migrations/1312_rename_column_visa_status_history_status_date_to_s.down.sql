-- Step M1312: Rename column visa_status_history.status_date to status_at
-- Direction: down
-- Findings: SCH-061-42e478dc
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column visa_status_history.status_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_status_history' AND table_schema = DATABASE() AND column_name = 'status_date'
-- Precheck: Column visa_status_history.status_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_status_history' AND table_schema = DATABASE() AND column_name = 'status_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_status_history` RENAME COLUMN `status_at` TO `status_date`, ALGORITHM=INPLACE, LOCK=NONE;
