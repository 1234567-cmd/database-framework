-- Step M776: Expand: add debit__dbintel_new decimal(17,4) on journal_entries and backfill
-- Direction: up
-- Findings: SCH-023-ec0cfb6c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table journal_entries exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_entries' AND table_schema = DATABASE()
-- Precheck: Column journal_entries.debit exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'journal_entries' AND table_schema = DATABASE() AND column_name = 'debit'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_entries` ADD COLUMN `debit__dbintel_new` decimal(17,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `journal_entries` SET `debit__dbintel_new` = `debit` WHERE `debit__dbintel_new` IS NULL AND `debit` IS NOT NULL LIMIT 1000;
