-- Step M1000: Add foreign key customers (customer_category_id) -> customer_categories
-- Direction: down
-- Findings: SCH-002-12044b8e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in customers (customer_category_id) referencing customer_categories (FK would fail)
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Table customer_categories exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_categories' AND table_schema = DATABASE()
-- Precheck: No orphan rows in customers (customer_category_id) referencing customer_categories (FK would fail). Expect 0: SELECT COUNT(*) FROM `customers` c LEFT JOIN `customer_categories` p ON c.`customer_category_id` = p.`id` WHERE c.`customer_category_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` DROP FOREIGN KEY `fk_customers_customer_category_id`;
