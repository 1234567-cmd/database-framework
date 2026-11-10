-- Step M271: Add column lcc_profile_templates.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-0746df6f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table lcc_profile_templates exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'lcc_profile_templates' AND table_schema = DATABASE()
-- Precheck: Column lcc_profile_templates.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'lcc_profile_templates' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `lcc_profile_templates` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
