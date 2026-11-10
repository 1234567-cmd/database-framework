-- Step M1103: Rename column customer_amends.bsp_payment_addon to is_bsp_payment_addon
-- Direction: down
-- Findings: SCH-060-95b2224d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_amends.bsp_payment_addon exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_amends' AND table_schema = DATABASE() AND column_name = 'bsp_payment_addon'
-- Precheck: Column customer_amends.is_bsp_payment_addon does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_amends' AND table_schema = DATABASE() AND column_name = 'is_bsp_payment_addon'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_amends` RENAME COLUMN `is_bsp_payment_addon` TO `bsp_payment_addon`, ALGORITHM=INPLACE, LOCK=NONE;
