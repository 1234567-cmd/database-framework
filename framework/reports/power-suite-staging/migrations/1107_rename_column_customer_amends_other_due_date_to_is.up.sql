-- Step M1107: Rename column customer_amends.other_due_date to is_other_due_date
-- Direction: up
-- Findings: SCH-060-626444af
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_amends.other_due_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_amends' AND table_schema = DATABASE() AND column_name = 'other_due_date'
-- Precheck: Column customer_amends.is_other_due_date does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_amends' AND table_schema = DATABASE() AND column_name = 'is_other_due_date'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_amends` RENAME COLUMN `other_due_date` TO `is_other_due_date`, ALGORITHM=INPLACE, LOCK=NONE;
