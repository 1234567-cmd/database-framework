-- Step M1115: Rename column customer_history.fee_id to fee_maintenance_id
-- Direction: down
-- Findings: SCH-058-7dede859
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_history.fee_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_history' AND table_schema = DATABASE() AND column_name = 'fee_id'
-- Precheck: Column customer_history.fee_maintenance_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_history' AND table_schema = DATABASE() AND column_name = 'fee_maintenance_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_history` RENAME COLUMN `fee_maintenance_id` TO `fee_id`, ALGORITHM=INPLACE, LOCK=NONE;
