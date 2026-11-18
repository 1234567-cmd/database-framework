-- Step M466: Add column ship_name_maintenances.updated_at timestamp
-- Direction: up
-- Findings: DE-005-00990638, SCH-044-c14b0e3d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table ship_name_maintenances exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'ship_name_maintenances' AND table_schema = DATABASE()
-- Precheck: Column ship_name_maintenances.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ship_name_maintenances' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `ship_name_maintenances` ADD COLUMN `updated_at` timestamp, ALGORITHM=INPLACE, LOCK=NONE;
