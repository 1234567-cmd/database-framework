-- Step M254: Add column iur_file_imports.updated_by varchar(255)
-- Direction: down
-- Findings: SCH-044-ee43b0a9
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table iur_file_imports exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iur_file_imports' AND table_schema = DATABASE()
-- Precheck: Column iur_file_imports.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iur_file_imports' AND table_schema = DATABASE() AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_file_imports` DROP COLUMN `updated_by`, ALGORITHM=INPLACE, LOCK=NONE;
