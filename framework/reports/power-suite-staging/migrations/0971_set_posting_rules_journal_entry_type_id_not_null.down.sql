-- Step M971: Set posting_rules.journal_entry_type_id NOT NULL
-- Direction: down
-- Findings: SCH-006-8f3a3e8e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in posting_rules.journal_entry_type_id (NOT NULL would fail)
-- Precheck: Table posting_rules exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'posting_rules' AND table_schema = DATABASE()
-- Precheck: Column posting_rules.journal_entry_type_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'posting_rules' AND table_schema = DATABASE() AND column_name = 'journal_entry_type_id'
-- Precheck: No NULLs in posting_rules.journal_entry_type_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `posting_rules` WHERE `journal_entry_type_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `posting_rules` MODIFY COLUMN `journal_entry_type_id` int NULL, ALGORITHM=INPLACE, LOCK=NONE;
