-- Step M881: Change type of receipts.total_amount to decimal(12,4) (widening)
-- Direction: down
-- Findings: SCH-023-be0fcb24
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table receipts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'receipts' AND table_schema = DATABASE()
-- Precheck: Column receipts.total_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'receipts' AND table_schema = DATABASE() AND column_name = 'total_amount'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipts` MODIFY COLUMN `total_amount` decimal(10,2) NULL, ALGORITHM=COPY, LOCK=SHARED;
