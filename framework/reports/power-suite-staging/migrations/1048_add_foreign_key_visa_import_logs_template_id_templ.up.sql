-- Step M1048: Add foreign key visa_import_logs (template_id) -> templates
-- Direction: up
-- Findings: SCH-002-25d04238
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in visa_import_logs (template_id) referencing templates (FK would fail)
-- Precheck: Table visa_import_logs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_import_logs' AND table_schema = DATABASE()
-- Precheck: Table templates exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'templates' AND table_schema = DATABASE()
-- Precheck: No orphan rows in visa_import_logs (template_id) referencing templates (FK would fail). Expect 0: SELECT COUNT(*) FROM `visa_import_logs` c LEFT JOIN `templates` p ON c.`template_id` = p.`id` WHERE c.`template_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_import_logs` ADD CONSTRAINT `fk_visa_import_logs_template_id` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`), ALGORITHM=COPY, LOCK=SHARED;
