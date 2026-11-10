-- Step M078: Add foreign key journal_lines (account_id) -> accounts
-- Direction: up
-- Findings: SCH-002-e4d31167
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in journal_lines (account_id) referencing accounts (FK would fail)
-- Precheck: Table journal_lines exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_lines' AND table_schema = DATABASE()
-- Precheck: Table accounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'accounts' AND table_schema = DATABASE()
-- Precheck: No orphan rows in journal_lines (account_id) referencing accounts (FK would fail). Expect 0: SELECT COUNT(*) FROM `journal_lines` c LEFT JOIN `accounts` p ON c.`account_id` = p.`id` WHERE c.`account_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_lines` ADD CONSTRAINT `fk_journal_lines_account_id` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`), ALGORITHM=COPY, LOCK=SHARED;
