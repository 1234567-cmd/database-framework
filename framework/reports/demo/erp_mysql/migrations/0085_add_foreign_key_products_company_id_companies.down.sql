-- Step M085: Add foreign key products (company_id) -> companies
-- Direction: down
-- Findings: SCH-002-950fd5ad
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in products (company_id) referencing companies (FK would fail)
-- Precheck: Table products exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'products' AND table_schema = DATABASE()
-- Precheck: Table companies exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'companies' AND table_schema = DATABASE()
-- Precheck: No orphan rows in products (company_id) referencing companies (FK would fail). Expect 0: SELECT COUNT(*) FROM `products` c LEFT JOIN `companies` p ON c.`company_id` = p.`id` WHERE c.`company_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `products` DROP FOREIGN KEY `fk_products_company_id`;
