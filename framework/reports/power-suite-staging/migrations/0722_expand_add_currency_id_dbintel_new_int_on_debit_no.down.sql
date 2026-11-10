-- Step M722: Expand: add currency_id__dbintel_new int on debit_notes and backfill
-- Direction: down
-- Findings: SCH-039-3ba2087e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: debit_notes.currency_id holds only integers
-- Precheck: Table debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'debit_notes' AND table_schema = DATABASE()
-- Precheck: Column debit_notes.currency_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'debit_notes' AND table_schema = DATABASE() AND column_name = 'currency_id'
-- Precheck: debit_notes.currency_id holds only integers. Expect 0: SELECT COUNT(*) FROM `debit_notes` WHERE `currency_id` IS NOT NULL AND (`currency_id` NOT REGEXP '^[+-]?[0-9]+$')
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` DROP COLUMN `currency_id__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
