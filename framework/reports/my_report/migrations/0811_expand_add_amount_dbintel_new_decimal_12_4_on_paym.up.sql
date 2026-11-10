-- Step M811: Expand: add amount__dbintel_new decimal(12,4) on payment_settlement_costs and backfill
-- Direction: up
-- Findings: SCH-023-8102c1dd
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_costs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_costs' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_costs.amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_costs' AND table_schema = DATABASE() AND column_name = 'amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_costs` ADD COLUMN `amount__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `payment_settlement_costs` SET `amount__dbintel_new` = `amount` WHERE `amount__dbintel_new` IS NULL AND `amount` IS NOT NULL LIMIT 1000;
