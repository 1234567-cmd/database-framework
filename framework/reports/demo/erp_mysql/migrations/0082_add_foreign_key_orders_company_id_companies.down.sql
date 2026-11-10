-- Step M082: Add foreign key orders (company_id) -> companies
-- Direction: down
-- Findings: SCH-002-4b414a10
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in orders (company_id) referencing companies (FK would fail)
-- Precheck: Table orders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'orders' AND table_schema = DATABASE()
-- Precheck: Table companies exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'companies' AND table_schema = DATABASE()
-- Precheck: No orphan rows in orders (company_id) referencing companies (FK would fail). Expect 0: SELECT COUNT(*) FROM `orders` c LEFT JOIN `companies` p ON c.`company_id` = p.`id` WHERE c.`company_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` DROP FOREIGN KEY `fk_orders_company_id`;
