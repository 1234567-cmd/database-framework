-- Step M054: Expand: add credit__dbintel_new decimal(19,4) on journal_lines and backfill
-- Direction: down
-- Findings: SCH-020-129ee72d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Could not write a generic check that journal_lines.credit converts from float to decimal(19,4). Verify conversion by hand before running.
-- Precheck: Table journal_lines exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_lines' AND table_schema = DATABASE()
-- Precheck: Column journal_lines.credit exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'journal_lines' AND table_schema = DATABASE() AND column_name = 'credit'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_lines` DROP COLUMN `credit__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
