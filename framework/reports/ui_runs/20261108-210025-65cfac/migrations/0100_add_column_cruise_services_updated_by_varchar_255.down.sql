-- Step M100: Add column cruise_services.updated_by varchar(255)
-- Direction: down
-- Findings: SCH-044-7766b77d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table cruise_services exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'cruise_services' AND table_schema = DATABASE()
-- Precheck: Column cruise_services.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cruise_services` DROP COLUMN `updated_by`, ALGORITHM=INPLACE, LOCK=NONE;
