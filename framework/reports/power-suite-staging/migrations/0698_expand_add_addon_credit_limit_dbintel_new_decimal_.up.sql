-- Step M698: Expand: add addon_credit_limit__dbintel_new decimal(12,4) on customers and backfill
-- Direction: up
-- Findings: SCH-023-b81e798b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Column customers.addon_credit_limit exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'addon_credit_limit'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` ADD COLUMN `addon_credit_limit__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `customers` SET `addon_credit_limit__dbintel_new` = `addon_credit_limit` WHERE `addon_credit_limit__dbintel_new` IS NULL AND `addon_credit_limit` IS NOT NULL LIMIT 1000;
