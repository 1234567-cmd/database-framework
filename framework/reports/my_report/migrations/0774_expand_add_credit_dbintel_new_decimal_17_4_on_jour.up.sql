-- Step M774: Expand: add credit__dbintel_new decimal(17,4) on journal_entries and backfill
-- Direction: up
-- Findings: SCH-023-436ac4fa
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table journal_entries exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_entries' AND table_schema = DATABASE()
-- Precheck: Column journal_entries.credit exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'journal_entries' AND table_schema = DATABASE() AND column_name = 'credit'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_entries` ADD COLUMN `credit__dbintel_new` decimal(17,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `journal_entries` SET `credit__dbintel_new` = `credit` WHERE `credit__dbintel_new` IS NULL AND `credit` IS NOT NULL LIMIT 1000;
