-- Step M166: Add column doc_issue_permissions.updated_at timestamp
-- Direction: up
-- Findings: DE-005-9ebc9f23
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table doc_issue_permissions exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'doc_issue_permissions' AND table_schema = DATABASE()
-- Precheck: Column doc_issue_permissions.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'doc_issue_permissions' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `doc_issue_permissions` ADD COLUMN `updated_at` timestamp, ALGORITHM=INPLACE, LOCK=NONE;
