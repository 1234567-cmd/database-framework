-- Step M348: Add column personal_genders.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-b942d946
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table personal_genders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'personal_genders' AND table_schema = DATABASE()
-- Precheck: Column personal_genders.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'personal_genders' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `personal_genders` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
