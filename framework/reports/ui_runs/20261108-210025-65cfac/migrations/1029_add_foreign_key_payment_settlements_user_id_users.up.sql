-- Step M1029: Add foreign key payment_settlements (user_id) -> users
-- Direction: up
-- Findings: SCH-002-e5c55f8a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in payment_settlements (user_id) referencing users (FK would fail)
-- Precheck: Table payment_settlements exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlements' AND table_schema = DATABASE()
-- Precheck: Table users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = DATABASE()
-- Precheck: No orphan rows in payment_settlements (user_id) referencing users (FK would fail). Expect 0: SELECT COUNT(*) FROM `payment_settlements` c LEFT JOIN `users` p ON c.`user_id` = p.`id` WHERE c.`user_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlements` ADD CONSTRAINT `fk_payment_settlements_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`), ALGORITHM=COPY, LOCK=SHARED;
