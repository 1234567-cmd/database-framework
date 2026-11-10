-- Step M928: Change type of supplier_amends.id to bigint (widening)
-- Direction: up
-- Findings: SCH-037-911f7520
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table supplier_amends exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'supplier_amends' AND table_schema = DATABASE()
-- Precheck: Column supplier_amends.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'supplier_amends' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `supplier_amends` MODIFY COLUMN `id` bigint NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
