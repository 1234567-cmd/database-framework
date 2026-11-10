-- Step M1002: Add foreign key customers (special_seat_id) -> special_seat
-- Direction: down
-- Findings: SCH-002-0563b878
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in customers (special_seat_id) referencing special_seat (FK would fail)
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Table special_seat exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'special_seat' AND table_schema = DATABASE()
-- Precheck: No orphan rows in customers (special_seat_id) referencing special_seat (FK would fail). Expect 0: SELECT COUNT(*) FROM `customers` c LEFT JOIN `special_seat` p ON c.`special_seat_id` = p.`id` WHERE c.`special_seat_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` DROP FOREIGN KEY `fk_customers_special_seat_id`;
