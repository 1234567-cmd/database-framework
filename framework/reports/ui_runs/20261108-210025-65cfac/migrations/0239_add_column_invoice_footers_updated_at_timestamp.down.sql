-- Step M239: Add column invoice_footers.updated_at timestamp
-- Direction: down
-- Findings: DE-005-d3f64f53, SCH-044-c39dd166
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table invoice_footers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoice_footers' AND table_schema = DATABASE()
-- Precheck: Column invoice_footers.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoice_footers' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoice_footers` DROP COLUMN `updated_at`, ALGORITHM=INPLACE, LOCK=NONE;
