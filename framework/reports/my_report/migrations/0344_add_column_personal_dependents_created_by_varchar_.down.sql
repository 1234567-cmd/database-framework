-- Step M344: Add column personal_dependents.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-370e7229
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table personal_dependents exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'personal_dependents' AND table_schema = DATABASE()
-- Precheck: Column personal_dependents.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'personal_dependents' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `personal_dependents` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
