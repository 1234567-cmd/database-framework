-- Step M074: Add foreign key accounts (company_id) -> companies
-- Direction: up
-- Findings: SCH-002-d694180a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in accounts (company_id) referencing companies (FK would fail)
-- Precheck: Table accounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'accounts' AND table_schema = DATABASE()
-- Precheck: Table companies exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'companies' AND table_schema = DATABASE()
-- Precheck: No orphan rows in accounts (company_id) referencing companies (FK would fail). Expect 0: SELECT COUNT(*) FROM `accounts` c LEFT JOIN `companies` p ON c.`company_id` = p.`id` WHERE c.`company_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `accounts` ADD CONSTRAINT `fk_accounts_company_id` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`), ALGORITHM=COPY, LOCK=SHARED;
