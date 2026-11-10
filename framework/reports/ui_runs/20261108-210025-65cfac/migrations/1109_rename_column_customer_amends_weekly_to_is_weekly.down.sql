-- Step M1109: Rename column customer_amends.weekly to is_weekly
-- Direction: down
-- Findings: SCH-060-b3dac58d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_amends.weekly exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_amends' AND table_schema = DATABASE() AND column_name = 'weekly'
-- Precheck: Column customer_amends.is_weekly does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_amends' AND table_schema = DATABASE() AND column_name = 'is_weekly'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_amends` RENAME COLUMN `is_weekly` TO `weekly`, ALGORITHM=INPLACE, LOCK=NONE;
