-- Step M1271: Rename column supplier_amends.credit_days to is_credit_days
-- Direction: up
-- Findings: SCH-060-ee202a84
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column supplier_amends.credit_days exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'supplier_amends' AND table_schema = DATABASE() AND column_name = 'credit_days'
-- Precheck: Column supplier_amends.is_credit_days does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'supplier_amends' AND table_schema = DATABASE() AND column_name = 'is_credit_days'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `supplier_amends` RENAME COLUMN `credit_days` TO `is_credit_days`, ALGORITHM=INPLACE, LOCK=NONE;
