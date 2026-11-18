-- Step M333: Add column permissions.updated_at timestamp
-- Direction: down
-- Findings: DE-005-b50a3c2e, SCH-044-c364b748
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table permissions exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'permissions' AND table_schema = DATABASE()
-- Precheck: Column permissions.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'permissions' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `permissions` DROP COLUMN `updated_at`, ALGORITHM=INPLACE, LOCK=NONE;
