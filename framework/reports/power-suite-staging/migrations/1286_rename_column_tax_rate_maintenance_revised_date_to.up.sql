-- Step M1286: Rename column tax_rate_maintenance.revised_date to revised_at
-- Direction: up
-- Findings: SCH-061-372d0f77
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column tax_rate_maintenance.revised_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tax_rate_maintenance' AND table_schema = DATABASE() AND column_name = 'revised_date'
-- Precheck: Column tax_rate_maintenance.revised_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tax_rate_maintenance' AND table_schema = DATABASE() AND column_name = 'revised_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `tax_rate_maintenance` RENAME COLUMN `revised_date` TO `revised_at`, ALGORITHM=INPLACE, LOCK=NONE;
