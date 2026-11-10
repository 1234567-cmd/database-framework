-- Step M751: Change type of invoice_discounts.discount_amount to decimal(12,4) (widening)
-- Direction: up
-- Findings: SCH-023-99ece3e0
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table invoice_discounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoice_discounts' AND table_schema = DATABASE()
-- Precheck: Column invoice_discounts.discount_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoice_discounts' AND table_schema = DATABASE() AND column_name = 'discount_amount'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoice_discounts` MODIFY COLUMN `discount_amount` decimal(12,4) NULL, ALGORITHM=COPY, LOCK=SHARED;
