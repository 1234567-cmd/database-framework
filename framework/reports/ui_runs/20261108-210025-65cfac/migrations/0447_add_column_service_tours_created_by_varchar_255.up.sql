-- Step M447: Add column service_tours.created_by varchar(255)
-- Direction: up
-- Findings: SCH-044-f27c728f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table service_tours exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_tours' AND table_schema = DATABASE()
-- Precheck: Column service_tours.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_tours' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` ADD COLUMN `created_by` varchar(255), ALGORITHM=INPLACE, LOCK=NONE;
