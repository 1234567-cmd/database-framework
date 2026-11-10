-- Step M848: Change type of payments.amount to decimal(12,4) (widening)
-- Direction: up
-- Findings: SCH-023-c30065ac
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payments exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payments' AND table_schema = DATABASE()
-- Precheck: Column payments.amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payments' AND table_schema = DATABASE() AND column_name = 'amount'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payments` MODIFY COLUMN `amount` decimal(12,4) NOT NULL, ALGORITHM=COPY, LOCK=SHARED;
