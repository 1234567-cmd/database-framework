-- Step M012: Add column airline_class_codes.created_at timestamp
-- Direction: down
-- Findings: SCH-044-480f8c9d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table airline_class_codes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'airline_class_codes' AND table_schema = DATABASE()
-- Precheck: Column airline_class_codes.created_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'airline_class_codes' AND table_schema = DATABASE() AND column_name = 'created_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `airline_class_codes` DROP COLUMN `created_at`, ALGORITHM=INPLACE, LOCK=NONE;
