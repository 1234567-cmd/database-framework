-- Step M429: Add column service_hajj_transports.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-fd77d739
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table service_hajj_transports exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_hajj_transports' AND table_schema = DATABASE()
-- Precheck: Column service_hajj_transports.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajj_transports' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hajj_transports` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
