-- Step M832: Expand: add credit__dbintel_new decimal(12,4) on payment_settlement_expenses and backfill
-- Direction: up
-- Findings: SCH-023-58dae922
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_expenses exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_expenses' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_expenses.credit exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_expenses' AND table_schema = DATABASE() AND column_name = 'credit'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_expenses` ADD COLUMN `credit__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `payment_settlement_expenses` SET `credit__dbintel_new` = `credit` WHERE `credit__dbintel_new` IS NULL AND `credit` IS NOT NULL LIMIT 1000;
