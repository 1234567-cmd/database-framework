-- Step M857: Change type of product_account_relations.id to bigint (widening)
-- Direction: down
-- Findings: SCH-037-a4783d1c
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table product_account_relations exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'product_account_relations' AND table_schema = DATABASE()
-- Precheck: Column product_account_relations.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'product_account_relations' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `product_account_relations` MODIFY COLUMN `id` int NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
