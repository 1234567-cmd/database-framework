-- Step M1273: Rename column supplier_amends.other_due_date to is_other_due_date
-- Direction: down
-- Findings: SCH-060-165706bf
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column supplier_amends.other_due_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'supplier_amends' AND table_schema = DATABASE() AND column_name = 'other_due_date'
-- Precheck: Column supplier_amends.is_other_due_date does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'supplier_amends' AND table_schema = DATABASE() AND column_name = 'is_other_due_date'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `supplier_amends` RENAME COLUMN `is_other_due_date` TO `other_due_date`, ALGORITHM=INPLACE, LOCK=NONE;
