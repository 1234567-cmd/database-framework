-- Step M1311: Rename column visa_ptc_maintenances.default_set to is_default_set
-- Direction: up
-- Findings: SCH-060-0e012217
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column visa_ptc_maintenances.default_set exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_ptc_maintenances' AND table_schema = DATABASE() AND column_name = 'default_set'
-- Precheck: Column visa_ptc_maintenances.is_default_set does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_ptc_maintenances' AND table_schema = DATABASE() AND column_name = 'is_default_set'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_ptc_maintenances` RENAME COLUMN `default_set` TO `is_default_set`, ALGORITHM=INPLACE, LOCK=NONE;
