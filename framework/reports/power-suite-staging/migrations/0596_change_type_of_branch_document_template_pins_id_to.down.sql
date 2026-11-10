-- Step M596: Change type of branch_document_template_pins.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-3a0eaf1b
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table branch_document_template_pins exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branch_document_template_pins' AND table_schema = DATABASE()
-- Precheck: Column branch_document_template_pins.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'branch_document_template_pins' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `branch_document_template_pins` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
