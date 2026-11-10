-- Step M824: Change type of payment_settlement_customer_transfers.base_amount to decimal(22,4) (widening)
-- Direction: down
-- Findings: SCH-023-9fbbabf4
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_customer_transfers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_customer_transfers' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_customer_transfers.base_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_customer_transfers' AND table_schema = DATABASE() AND column_name = 'base_amount'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_customer_transfers` MODIFY COLUMN `base_amount` decimal(20,2) NULL COMMENT 'Amount in base currency', ALGORITHM=COPY, LOCK=SHARED;
