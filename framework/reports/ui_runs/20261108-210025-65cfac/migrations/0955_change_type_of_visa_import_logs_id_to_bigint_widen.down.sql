-- Step M955: Change type of visa_import_logs.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-d5cbfd7e
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table visa_import_logs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_import_logs' AND table_schema = DATABASE()
-- Precheck: Column visa_import_logs.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_import_logs' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_import_logs` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
