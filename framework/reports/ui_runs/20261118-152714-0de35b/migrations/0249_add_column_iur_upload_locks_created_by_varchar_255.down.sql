-- Step M249: Add column iur_upload_locks.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-7f7a280b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table iur_upload_locks exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iur_upload_locks' AND table_schema = DATABASE()
-- Precheck: Column iur_upload_locks.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iur_upload_locks' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_upload_locks` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
