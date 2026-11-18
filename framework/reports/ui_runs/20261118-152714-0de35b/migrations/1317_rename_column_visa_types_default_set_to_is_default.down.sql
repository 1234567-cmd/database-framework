-- Step M1317: Rename column visa_types.default_set to is_default_set
-- Direction: down
-- Findings: SCH-060-47e0d889
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column visa_types.default_set exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_types' AND table_schema = DATABASE() AND column_name = 'default_set'
-- Precheck: Column visa_types.is_default_set does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_types' AND table_schema = DATABASE() AND column_name = 'is_default_set'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_types` RENAME COLUMN `is_default_set` TO `default_set`, ALGORITHM=INPLACE, LOCK=NONE;
