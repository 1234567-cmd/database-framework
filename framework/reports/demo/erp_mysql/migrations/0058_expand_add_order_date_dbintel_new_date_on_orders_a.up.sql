-- Step M058: Expand: add order_date__dbintel_new date on orders and backfill
-- Direction: up
-- Findings: SCH-031-7a0dc170
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: orders.order_date holds ISO dates
-- Precheck: Table orders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'orders' AND table_schema = DATABASE()
-- Precheck: Column orders.order_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'orders' AND table_schema = DATABASE() AND column_name = 'order_date'
-- Precheck: orders.order_date holds ISO dates. Expect 0: SELECT COUNT(*) FROM `orders` WHERE `order_date` IS NOT NULL AND (`order_date` NOT REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}')
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` ADD COLUMN `order_date__dbintel_new` date, ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `orders` SET `order_date__dbintel_new` = `order_date` WHERE `order_date__dbintel_new` IS NULL AND `order_date` IS NOT NULL LIMIT 1000;
