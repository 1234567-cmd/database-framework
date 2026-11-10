-- Step M844: Expand: add overpay_amount__dbintel_new decimal(12,4) on payment_settlement_payments and backfill
-- Direction: up
-- Findings: SCH-023-36f8b67d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_payments exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_payments' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_payments.overpay_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_payments' AND table_schema = DATABASE() AND column_name = 'overpay_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_payments` ADD COLUMN `overpay_amount__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `payment_settlement_payments` SET `overpay_amount__dbintel_new` = `overpay_amount` WHERE `overpay_amount__dbintel_new` IS NULL AND `overpay_amount` IS NOT NULL LIMIT 1000;
