-- Step M620: Change type of credit_control_pccs.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-a5966f67
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table credit_control_pccs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'credit_control_pccs' AND table_schema = DATABASE()
-- Precheck: Column credit_control_pccs.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'credit_control_pccs' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_control_pccs` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
