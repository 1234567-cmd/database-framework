-- Step M674: Expand: add base_amount__dbintel_new decimal(12,4) on customer_deposits and backfill
-- Direction: up
-- Findings: SCH-023-73706aae
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_deposits' AND table_schema = DATABASE()
-- Precheck: Column customer_deposits.base_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_deposits' AND table_schema = DATABASE() AND column_name = 'base_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposits` ADD COLUMN `base_amount__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `customer_deposits` SET `base_amount__dbintel_new` = `base_amount` WHERE `base_amount__dbintel_new` IS NULL AND `base_amount` IS NOT NULL LIMIT 1000;
