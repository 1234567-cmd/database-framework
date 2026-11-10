-- Step M828: Expand: add base_amount__dbintel_new decimal(12,4) on payment_settlement_debit_notes and backfill
-- Direction: down
-- Findings: SCH-023-99dafae1
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_debit_notes' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_debit_notes.base_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_debit_notes' AND table_schema = DATABASE() AND column_name = 'base_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_debit_notes` DROP COLUMN `base_amount__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
