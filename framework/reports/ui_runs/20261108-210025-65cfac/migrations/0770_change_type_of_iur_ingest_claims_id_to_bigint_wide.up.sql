-- Step M770: Change type of iur_ingest_claims.id to bigint (widening)
-- Direction: up
-- Findings: SCH-037-5b1e3371
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table iur_ingest_claims exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iur_ingest_claims' AND table_schema = DATABASE()
-- Precheck: Column iur_ingest_claims.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iur_ingest_claims' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_ingest_claims` MODIFY COLUMN `id` bigint NOT NULL AUTO_INCREMENT, ALGORITHM=COPY, LOCK=SHARED;
