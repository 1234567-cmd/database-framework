-- Step M179: Add column fee_maintenances.created_by varchar(255)
-- Direction: up
-- Findings: SCH-044-ba4c7768
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table fee_maintenances exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fee_maintenances' AND table_schema = DATABASE()
-- Precheck: Column fee_maintenances.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_maintenances' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_maintenances` ADD COLUMN `created_by` varchar(255), ALGORITHM=INPLACE, LOCK=NONE;
