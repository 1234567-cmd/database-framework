-- Step M601: Change type of coa_templates.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-21546596
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table coa_templates exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'coa_templates' AND table_schema = DATABASE()
-- Precheck: Column coa_templates.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'coa_templates' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `coa_templates` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
