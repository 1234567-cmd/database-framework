-- Step M752: Change type of invoice_discounts.id to bigint (widening)
-- Direction: up
-- Findings: SCH-037-6d8b8e63
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table invoice_discounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoice_discounts' AND table_schema = DATABASE()
-- Precheck: Column invoice_discounts.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoice_discounts' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoice_discounts` MODIFY COLUMN `id` bigint NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
