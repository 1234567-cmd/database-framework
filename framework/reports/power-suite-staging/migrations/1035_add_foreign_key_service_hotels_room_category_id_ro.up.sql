-- Step M1035: Add foreign key service_hotels (room_category_id) -> room_categories
-- Direction: up
-- Findings: SCH-002-957db0c2
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in service_hotels (room_category_id) referencing room_categories (FK would fail)
-- Precheck: Table service_hotels exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_hotels' AND table_schema = DATABASE()
-- Precheck: Table room_categories exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'room_categories' AND table_schema = DATABASE()
-- Precheck: No orphan rows in service_hotels (room_category_id) referencing room_categories (FK would fail). Expect 0: SELECT COUNT(*) FROM `service_hotels` c LEFT JOIN `room_categories` p ON c.`room_category_id` = p.`id` WHERE c.`room_category_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hotels` ADD CONSTRAINT `fk_service_hotels_room_category_id` FOREIGN KEY (`room_category_id`) REFERENCES `room_categories` (`id`), ALGORITHM=COPY, LOCK=SHARED;
