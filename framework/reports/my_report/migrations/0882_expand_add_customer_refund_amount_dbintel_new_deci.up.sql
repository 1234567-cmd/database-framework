-- Step M882: Expand: add customer_refund_amount__dbintel_new decimal(17,4) on refunds and backfill
-- Direction: up
-- Findings: SCH-023-b537a3d6
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table refunds exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'refunds' AND table_schema = DATABASE()
-- Precheck: Column refunds.customer_refund_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'refunds' AND table_schema = DATABASE() AND column_name = 'customer_refund_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` ADD COLUMN `customer_refund_amount__dbintel_new` decimal(17,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `refunds` SET `customer_refund_amount__dbintel_new` = `customer_refund_amount` WHERE `customer_refund_amount__dbintel_new` IS NULL AND `customer_refund_amount` IS NOT NULL LIMIT 1000;
