-- Step M457: Add column service_types.updated_by varchar(255)
-- Direction: down
-- Findings: SCH-044-06b6dce9
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table service_types exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_types' AND table_schema = DATABASE()
-- Precheck: Column service_types.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_types' AND table_schema = DATABASE() AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_types` DROP COLUMN `updated_by`, ALGORITHM=INPLACE, LOCK=NONE;
