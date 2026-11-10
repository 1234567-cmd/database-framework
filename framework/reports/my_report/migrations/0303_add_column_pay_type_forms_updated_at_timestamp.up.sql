-- Step M303: Add column pay_type_forms.updated_at timestamp
-- Direction: up
-- Findings: DE-005-a048cff3, SCH-044-051b0776
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table pay_type_forms exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'pay_type_forms' AND table_schema = DATABASE()
-- Precheck: Column pay_type_forms.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'pay_type_forms' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `pay_type_forms` ADD COLUMN `updated_at` timestamp, ALGORITHM=INPLACE, LOCK=NONE;
