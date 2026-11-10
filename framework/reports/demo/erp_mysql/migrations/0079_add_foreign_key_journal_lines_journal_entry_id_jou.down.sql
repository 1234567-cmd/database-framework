-- Step M079: Add foreign key journal_lines (journal_entry_id) -> journal_entries
-- Direction: down
-- Findings: SCH-002-f5d88d13
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in journal_lines (journal_entry_id) referencing journal_entries (FK would fail)
-- Precheck: Table journal_lines exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_lines' AND table_schema = DATABASE()
-- Precheck: Table journal_entries exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_entries' AND table_schema = DATABASE()
-- Precheck: No orphan rows in journal_lines (journal_entry_id) referencing journal_entries (FK would fail). Expect 0: SELECT COUNT(*) FROM `journal_lines` c LEFT JOIN `journal_entries` p ON c.`journal_entry_id` = p.`id` WHERE c.`journal_entry_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_lines` DROP FOREIGN KEY `fk_journal_lines_journal_entry_id`;
