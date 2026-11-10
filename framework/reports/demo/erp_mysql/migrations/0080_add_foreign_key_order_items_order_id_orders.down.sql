-- Step M080: Add foreign key order_items (order_id) -> orders
-- Direction: down
-- Findings: SCH-002-a89dacde
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in order_items (order_id) referencing orders (FK would fail)
-- Precheck: Table order_items exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'order_items' AND table_schema = DATABASE()
-- Precheck: Table orders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'orders' AND table_schema = DATABASE()
-- Precheck: No orphan rows in order_items (order_id) referencing orders (FK would fail). Expect 0: SELECT COUNT(*) FROM `order_items` c LEFT JOIN `orders` p ON c.`order_id` = p.`id` WHERE c.`order_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `order_items` DROP FOREIGN KEY `fk_order_items_order_id`;
