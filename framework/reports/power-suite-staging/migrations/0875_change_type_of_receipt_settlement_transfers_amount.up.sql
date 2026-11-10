-- Step M875: Change type of receipt_settlement_transfers.amount to decimal(14,4) (widening)
-- Direction: up
-- Findings: SCH-023-d306710f
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table receipt_settlement_transfers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'receipt_settlement_transfers' AND table_schema = DATABASE()
-- Precheck: Column receipt_settlement_transfers.amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'receipt_settlement_transfers' AND table_schema = DATABASE() AND column_name = 'amount'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipt_settlement_transfers` MODIFY COLUMN `amount` decimal(14,4) NULL, ALGORITHM=COPY, LOCK=SHARED;
