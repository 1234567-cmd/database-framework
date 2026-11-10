-- Step M061: Expand: add total__dbintel_new decimal(19,4) on orders and backfill
-- Direction: down
-- Findings: SCH-020-bc1e8a52
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Could not write a generic check that orders.total converts from float to decimal(19,4). Verify conversion by hand before running.
-- Precheck: Table orders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'orders' AND table_schema = DATABASE()
-- Precheck: Column orders.total exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'orders' AND table_schema = DATABASE() AND column_name = 'total'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` DROP COLUMN `total__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
