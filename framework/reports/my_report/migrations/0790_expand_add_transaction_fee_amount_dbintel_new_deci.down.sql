-- Step M790: Expand: add transaction_fee_amount__dbintel_new decimal(18,4) on maintenance_fee_groups and backfill
-- Direction: down
-- Findings: SCH-032-559100a5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: maintenance_fee_groups.transaction_fee_amount holds only numbers
-- Precheck: Table maintenance_fee_groups exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE()
-- Precheck: Column maintenance_fee_groups.transaction_fee_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE() AND column_name = 'transaction_fee_amount'
-- Precheck: maintenance_fee_groups.transaction_fee_amount holds only numbers. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE `transaction_fee_amount` IS NOT NULL AND (`transaction_fee_amount` NOT REGEXP '^[+-]?[0-9]+([.][0-9]+)?$')
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` DROP COLUMN `transaction_fee_amount__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
