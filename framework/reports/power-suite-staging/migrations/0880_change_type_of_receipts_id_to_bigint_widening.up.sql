-- Step M880: Change type of receipts.id to bigint (widening)
-- Direction: up
-- Findings: SCH-037-018fdc9c
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table receipts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'receipts' AND table_schema = DATABASE()
-- Precheck: Column receipts.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'receipts' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipts` MODIFY COLUMN `id` bigint NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
