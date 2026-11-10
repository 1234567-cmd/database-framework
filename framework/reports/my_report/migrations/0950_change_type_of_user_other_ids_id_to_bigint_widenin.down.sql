-- Step M950: Change type of user_other_ids.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-e50f8f2c
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table user_other_ids exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'user_other_ids' AND table_schema = DATABASE()
-- Precheck: Column user_other_ids.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'user_other_ids' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `user_other_ids` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
