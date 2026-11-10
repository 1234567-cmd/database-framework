-- Step M769: Change type of iur_file_imports.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-c58a55f2
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table iur_file_imports exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iur_file_imports' AND table_schema = DATABASE()
-- Precheck: Column iur_file_imports.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iur_file_imports' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_file_imports` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
