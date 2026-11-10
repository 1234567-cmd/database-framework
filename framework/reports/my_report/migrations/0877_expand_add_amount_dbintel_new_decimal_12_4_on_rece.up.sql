-- Step M877: Expand: add amount__dbintel_new decimal(12,4) on receipt_settlements and backfill
-- Direction: up
-- Findings: SCH-023-58bb57ec
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table receipt_settlements exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'receipt_settlements' AND table_schema = DATABASE()
-- Precheck: Column receipt_settlements.amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'receipt_settlements' AND table_schema = DATABASE() AND column_name = 'amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipt_settlements` ADD COLUMN `amount__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `receipt_settlements` SET `amount__dbintel_new` = `amount` WHERE `amount__dbintel_new` IS NULL AND `amount` IS NOT NULL LIMIT 1000;
