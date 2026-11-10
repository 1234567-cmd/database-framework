-- Step M1013: Add foreign key iur_file_imports (order_id) -> orders
-- Direction: up
-- Findings: SCH-002-5d5a4921
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in iur_file_imports (order_id) referencing orders (FK would fail)
-- Precheck: Table iur_file_imports exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iur_file_imports' AND table_schema = DATABASE()
-- Precheck: Table orders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'orders' AND table_schema = DATABASE()
-- Precheck: No orphan rows in iur_file_imports (order_id) referencing orders (FK would fail). Expect 0: SELECT COUNT(*) FROM `iur_file_imports` c LEFT JOIN `orders` p ON c.`order_id` = p.`id` WHERE c.`order_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_file_imports` ADD CONSTRAINT `fk_iur_file_imports_order_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`), ALGORITHM=COPY, LOCK=SHARED;
