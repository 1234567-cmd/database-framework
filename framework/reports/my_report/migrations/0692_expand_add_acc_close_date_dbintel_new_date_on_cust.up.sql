-- Step M692: Expand: add acc_close_date__dbintel_new date on customers and backfill
-- Direction: up
-- Findings: SCH-031-188ab9df
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: customers.acc_close_date holds ISO dates
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Column customers.acc_close_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'acc_close_date'
-- Precheck: customers.acc_close_date holds ISO dates. Expect 0: SELECT COUNT(*) FROM `customers` WHERE `acc_close_date` IS NOT NULL AND (`acc_close_date` NOT REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}')
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` ADD COLUMN `acc_close_date__dbintel_new` date, ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `customers` SET `acc_close_date__dbintel_new` = `acc_close_date` WHERE `acc_close_date__dbintel_new` IS NULL AND `acc_close_date` IS NOT NULL LIMIT 1000;
