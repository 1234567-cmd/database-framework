-- Step M602: Expand: add id__dbintel_new bigint on cost_taxes and backfill
-- Direction: down
-- Findings: SCH-037-699d1eb5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table cost_taxes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'cost_taxes' AND table_schema = DATABASE()
-- Precheck: Column cost_taxes.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cost_taxes' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cost_taxes` DROP COLUMN `id__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
