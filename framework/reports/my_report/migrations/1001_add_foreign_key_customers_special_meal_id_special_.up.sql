-- Step M1001: Add foreign key customers (special_meal_id) -> special_meal
-- Direction: up
-- Findings: SCH-002-ba1f3386
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in customers (special_meal_id) referencing special_meal (FK would fail)
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Table special_meal exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'special_meal' AND table_schema = DATABASE()
-- Precheck: No orphan rows in customers (special_meal_id) referencing special_meal (FK would fail). Expect 0: SELECT COUNT(*) FROM `customers` c LEFT JOIN `special_meal` p ON c.`special_meal_id` = p.`id` WHERE c.`special_meal_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` ADD CONSTRAINT `fk_customers_special_meal_id` FOREIGN KEY (`special_meal_id`) REFERENCES `special_meal` (`id`), ALGORITHM=COPY, LOCK=SHARED;
