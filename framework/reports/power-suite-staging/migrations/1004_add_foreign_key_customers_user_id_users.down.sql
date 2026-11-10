-- Step M1004: Add foreign key customers (user_id) -> users
-- Direction: down
-- Findings: SCH-002-afb46f31
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in customers (user_id) referencing users (FK would fail)
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Table users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = DATABASE()
-- Precheck: No orphan rows in customers (user_id) referencing users (FK would fail). Expect 0: SELECT COUNT(*) FROM `customers` c LEFT JOIN `users` p ON c.`user_id` = p.`id` WHERE c.`user_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` DROP FOREIGN KEY `fk_customers_user_id`;
