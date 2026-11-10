-- Step M989: Add foreign key bank_accounts (chart_of_account_id) -> chart_of_accounts
-- Direction: down
-- Findings: SCH-002-787aff63
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in bank_accounts (chart_of_account_id) referencing chart_of_accounts (FK would fail)
-- Precheck: Table bank_accounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'bank_accounts' AND table_schema = DATABASE()
-- Precheck: Table chart_of_accounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'chart_of_accounts' AND table_schema = DATABASE()
-- Precheck: No orphan rows in bank_accounts (chart_of_account_id) referencing chart_of_accounts (FK would fail). Expect 0: SELECT COUNT(*) FROM `bank_accounts` c LEFT JOIN `chart_of_accounts` p ON c.`chart_of_account_id` = p.`id` WHERE c.`chart_of_account_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `bank_accounts` DROP FOREIGN KEY `fk_bank_accounts_chart_of_account_id`;
