-- Step M1288: Rename column templates.separator to separator_value
-- Direction: up
-- Findings: SCH-050-adb41dcf
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column templates.separator exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'templates' AND table_schema = DATABASE() AND column_name = 'separator'
-- Precheck: Column templates.separator_value does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'templates' AND table_schema = DATABASE() AND column_name = 'separator_value'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `templates` RENAME COLUMN `separator` TO `separator_value`, ALGORITHM=INPLACE, LOCK=NONE;
