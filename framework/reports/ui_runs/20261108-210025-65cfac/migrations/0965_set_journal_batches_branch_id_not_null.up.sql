-- Step M965: Set journal_batches.branch_id NOT NULL
-- Direction: up
-- Findings: SCH-006-09558db9
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in journal_batches.branch_id (NOT NULL would fail)
-- Precheck: Table journal_batches exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_batches' AND table_schema = DATABASE()
-- Precheck: Column journal_batches.branch_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'journal_batches' AND table_schema = DATABASE() AND column_name = 'branch_id'
-- Precheck: No NULLs in journal_batches.branch_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `journal_batches` WHERE `branch_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_batches` MODIFY COLUMN `branch_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
