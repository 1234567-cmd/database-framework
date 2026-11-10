-- Step M064: Expand: add amount__dbintel_new decimal(19,4) on payments and backfill
-- Direction: up
-- Findings: SCH-020-b9ce260d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Could not write a generic check that payments.amount converts from float to decimal(19,4). Verify conversion by hand before running.
-- Precheck: Table payments exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payments' AND table_schema = DATABASE()
-- Precheck: Column payments.amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payments' AND table_schema = DATABASE() AND column_name = 'amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payments` ADD COLUMN `amount__dbintel_new` decimal(19,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `payments` SET `amount__dbintel_new` = `amount` WHERE `amount__dbintel_new` IS NULL AND `amount` IS NOT NULL LIMIT 1000;
