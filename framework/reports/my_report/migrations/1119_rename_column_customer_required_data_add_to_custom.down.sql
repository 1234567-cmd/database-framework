-- Step M1119: Rename column customer_required_data.add_to_customer to is_add_to_customer
-- Direction: down
-- Findings: SCH-060-fb9144e2
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_required_data.add_to_customer exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data' AND table_schema = DATABASE() AND column_name = 'add_to_customer'
-- Precheck: Column customer_required_data.is_add_to_customer does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data' AND table_schema = DATABASE() AND column_name = 'is_add_to_customer'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data` RENAME COLUMN `is_add_to_customer` TO `add_to_customer`, ALGORITHM=INPLACE, LOCK=NONE;
