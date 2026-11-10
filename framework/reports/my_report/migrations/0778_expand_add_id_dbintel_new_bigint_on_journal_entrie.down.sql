-- Step M778: Expand: add id__dbintel_new bigint on journal_entries and backfill
-- Direction: down
-- Findings: SCH-037-56a89689
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table journal_entries exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_entries' AND table_schema = DATABASE()
-- Precheck: Column journal_entries.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'journal_entries' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_entries` DROP COLUMN `id__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
