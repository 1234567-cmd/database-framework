-- Step M177: Add column fee_main_product_codes.updated_at timestamp
-- Direction: up
-- Findings: DE-005-f0bf3003
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table fee_main_product_codes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fee_main_product_codes' AND table_schema = DATABASE()
-- Precheck: Column fee_main_product_codes.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_main_product_codes' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_main_product_codes` ADD COLUMN `updated_at` timestamp, ALGORITHM=INPLACE, LOCK=NONE;
