-- Step M003: Add column admin_audit_log.updated_by varchar(255)
-- Direction: up
-- Findings: SCH-044-bdfb37ca
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table admin_audit_log exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'admin_audit_log' AND table_schema = DATABASE()
-- Precheck: Column admin_audit_log.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'admin_audit_log' AND table_schema = DATABASE() AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `admin_audit_log` ADD COLUMN `updated_by` varchar(255), ALGORITHM=INPLACE, LOCK=NONE;
