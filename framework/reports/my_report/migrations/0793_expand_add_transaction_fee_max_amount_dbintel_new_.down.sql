-- Step M793: Expand: add transaction_fee_max_amount__dbintel_new bigint on maintenance_fee_groups and backfill
-- Direction: down
-- Findings: SCH-032-3d03ea7e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: maintenance_fee_groups.transaction_fee_max_amount holds only integers
-- Precheck: Table maintenance_fee_groups exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE()
-- Precheck: Column maintenance_fee_groups.transaction_fee_max_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE() AND column_name = 'transaction_fee_max_amount'
-- Precheck: maintenance_fee_groups.transaction_fee_max_amount holds only integers. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE `transaction_fee_max_amount` IS NOT NULL AND (`transaction_fee_max_amount` NOT REGEXP '^[+-]?[0-9]+$')
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` DROP COLUMN `transaction_fee_max_amount__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
