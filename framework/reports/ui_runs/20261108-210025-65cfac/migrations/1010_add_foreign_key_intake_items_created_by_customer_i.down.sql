-- Step M1010: Add foreign key intake_items (created_by_customer_id) -> customers
-- Direction: down
-- Findings: SCH-002-1a321c88
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in intake_items (created_by_customer_id) referencing customers (FK would fail)
-- Precheck: Table intake_items exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'intake_items' AND table_schema = DATABASE()
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: No orphan rows in intake_items (created_by_customer_id) referencing customers (FK would fail). Expect 0: SELECT COUNT(*) FROM `intake_items` c LEFT JOIN `customers` p ON c.`created_by_customer_id` = p.`id` WHERE c.`created_by_customer_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `intake_items` DROP FOREIGN KEY `fk_intake_items_created_by_customer_id`;
