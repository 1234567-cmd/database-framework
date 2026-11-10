-- Step M1050: Add foreign key visa_maintenance_history (user_id) -> users
-- Direction: down
-- Findings: SCH-002-ec2130e2
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in visa_maintenance_history (user_id) referencing users (FK would fail)
-- Precheck: Table visa_maintenance_history exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_maintenance_history' AND table_schema = DATABASE()
-- Precheck: Table users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = DATABASE()
-- Precheck: No orphan rows in visa_maintenance_history (user_id) referencing users (FK would fail). Expect 0: SELECT COUNT(*) FROM `visa_maintenance_history` c LEFT JOIN `users` p ON c.`user_id` = p.`id` WHERE c.`user_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_maintenance_history` DROP FOREIGN KEY `fk_visa_maintenance_history_user_id`;
