-- Step M988: Add foreign key admin_audit_log (admin_user_id) -> admin_users
-- Direction: down
-- Findings: SCH-002-e6cedd12
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in admin_audit_log (admin_user_id) referencing admin_users (FK would fail)
-- Precheck: Table admin_audit_log exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'admin_audit_log' AND table_schema = DATABASE()
-- Precheck: Table admin_users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'admin_users' AND table_schema = DATABASE()
-- Precheck: No orphan rows in admin_audit_log (admin_user_id) referencing admin_users (FK would fail). Expect 0: SELECT COUNT(*) FROM `admin_audit_log` c LEFT JOIN `admin_users` p ON c.`admin_user_id` = p.`id` WHERE c.`admin_user_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `admin_audit_log` DROP FOREIGN KEY `fk_admin_audit_log_admin_user_id`;
