-- Step M690: Change type of customer_special_handling.id to bigint (widening)
-- Direction: up
-- Findings: SCH-037-dd440897
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_special_handling exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_special_handling' AND table_schema = DATABASE()
-- Precheck: Column customer_special_handling.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_special_handling' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_special_handling` MODIFY COLUMN `id` bigint NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
