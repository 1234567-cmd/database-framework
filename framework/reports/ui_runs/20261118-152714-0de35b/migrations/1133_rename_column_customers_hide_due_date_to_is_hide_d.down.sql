-- Step M1133: Rename column customers.hide_due_date to is_hide_due_date
-- Direction: down
-- Findings: SCH-060-477ae7fd
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customers.hide_due_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'hide_due_date'
-- Precheck: Column customers.is_hide_due_date does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'is_hide_due_date'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` RENAME COLUMN `is_hide_due_date` TO `hide_due_date`, ALGORITHM=INPLACE, LOCK=NONE;
