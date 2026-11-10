-- Step M952: Expand: add cost_amount__dbintel_new decimal(17,4) on visa_code_maintenance and backfill
-- Direction: up
-- Findings: SCH-023-c639be29
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table visa_code_maintenance exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_code_maintenance' AND table_schema = DATABASE()
-- Precheck: Column visa_code_maintenance.cost_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_code_maintenance' AND table_schema = DATABASE() AND column_name = 'cost_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_code_maintenance` ADD COLUMN `cost_amount__dbintel_new` decimal(17,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `visa_code_maintenance` SET `cost_amount__dbintel_new` = `cost_amount` WHERE `cost_amount__dbintel_new` IS NULL AND `cost_amount` IS NOT NULL LIMIT 1000;
