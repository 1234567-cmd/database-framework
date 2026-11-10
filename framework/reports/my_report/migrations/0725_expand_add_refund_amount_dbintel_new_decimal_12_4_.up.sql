-- Step M725: Expand: add refund_amount__dbintel_new decimal(12,4) on debit_notes and backfill
-- Direction: up
-- Findings: SCH-023-b57fb54b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'debit_notes' AND table_schema = DATABASE()
-- Precheck: Column debit_notes.refund_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'debit_notes' AND table_schema = DATABASE() AND column_name = 'refund_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` ADD COLUMN `refund_amount__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `debit_notes` SET `refund_amount__dbintel_new` = `refund_amount` WHERE `refund_amount__dbintel_new` IS NULL AND `refund_amount` IS NOT NULL LIMIT 1000;
