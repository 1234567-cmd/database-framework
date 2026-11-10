-- Step M658: Change type of customer_credit_terms.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-48e4c9bf
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_credit_terms exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_credit_terms' AND table_schema = DATABASE()
-- Precheck: Column customer_credit_terms.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_credit_terms' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_credit_terms` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
