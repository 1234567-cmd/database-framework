-- Step M580: Add column visa_status_history.updated_by varchar(255)
-- Direction: up
-- Findings: SCH-044-58efeea4
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table visa_status_history exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_status_history' AND table_schema = DATABASE()
-- Precheck: Column visa_status_history.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_status_history' AND table_schema = DATABASE() AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_status_history` ADD COLUMN `updated_by` varchar(255), ALGORITHM=INPLACE, LOCK=NONE;
