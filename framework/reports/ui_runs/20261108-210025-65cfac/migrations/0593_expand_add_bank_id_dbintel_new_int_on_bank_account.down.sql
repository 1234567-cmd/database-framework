-- Step M593: Expand: add bank_id__dbintel_new int on bank_accounts and backfill
-- Direction: down
-- Findings: SCH-039-a836d0c5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: bank_accounts.bank_id holds only integers
-- Precheck: Table bank_accounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'bank_accounts' AND table_schema = DATABASE()
-- Precheck: Column bank_accounts.bank_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'bank_accounts' AND table_schema = DATABASE() AND column_name = 'bank_id'
-- Precheck: bank_accounts.bank_id holds only integers. Expect 0: SELECT COUNT(*) FROM `bank_accounts` WHERE `bank_id` IS NOT NULL AND (`bank_id` NOT REGEXP '^[+-]?[0-9]+$')
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `bank_accounts` DROP COLUMN `bank_id__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
