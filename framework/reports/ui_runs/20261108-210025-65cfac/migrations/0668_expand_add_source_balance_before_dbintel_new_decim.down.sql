-- Step M668: Expand: add source_balance_before__dbintel_new decimal(14,4) on customer_deposit_transfers and backfill
-- Direction: down
-- Findings: SCH-023-894a1f2e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_deposit_transfers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_deposit_transfers' AND table_schema = DATABASE()
-- Precheck: Column customer_deposit_transfers.source_balance_before exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_deposit_transfers' AND table_schema = DATABASE() AND column_name = 'source_balance_before'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposit_transfers` DROP COLUMN `source_balance_before__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
