-- Step M994: Add foreign key customer_amends (customer_id) -> customers
-- Direction: up
-- Findings: SCH-002-7dcf77b8
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in customer_amends (customer_id) referencing customers (FK would fail)
-- Precheck: Table customer_amends exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_amends' AND table_schema = DATABASE()
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: No orphan rows in customer_amends (customer_id) referencing customers (FK would fail). Expect 0: SELECT COUNT(*) FROM `customer_amends` c LEFT JOIN `customers` p ON c.`customer_id` = p.`id` WHERE c.`customer_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_amends` ADD CONSTRAINT `fk_customer_amends_customer_id` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`), ALGORITHM=COPY, LOCK=SHARED;
