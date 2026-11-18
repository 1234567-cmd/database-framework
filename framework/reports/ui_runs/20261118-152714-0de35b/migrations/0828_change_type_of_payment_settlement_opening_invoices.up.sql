-- Step M828: Change type of payment_settlement_opening_invoices.amount to decimal(22,4) (widening)
-- Direction: up
-- Findings: SCH-023-7851db6d
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_opening_invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_opening_invoices' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_opening_invoices.amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_opening_invoices' AND table_schema = DATABASE() AND column_name = 'amount'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_opening_invoices` MODIFY COLUMN `amount` decimal(22,4) NOT NULL DEFAULT '0.00' COMMENT 'Credit paid back, positive, in base currency', ALGORITHM=COPY, LOCK=SHARED;
