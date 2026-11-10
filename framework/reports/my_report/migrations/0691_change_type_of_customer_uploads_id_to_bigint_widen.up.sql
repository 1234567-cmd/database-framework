-- Step M691: Change type of customer_uploads.id to bigint (widening)
-- Direction: up
-- Findings: SCH-037-7a0edcf1
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_uploads exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_uploads' AND table_schema = DATABASE()
-- Precheck: Column customer_uploads.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_uploads' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_uploads` MODIFY COLUMN `id` bigint NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
