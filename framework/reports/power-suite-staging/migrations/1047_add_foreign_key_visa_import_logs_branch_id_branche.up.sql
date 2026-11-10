-- Step M1047: Add foreign key visa_import_logs (branch_id) -> branches
-- Direction: up
-- Findings: SCH-002-87e9ec90
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in visa_import_logs (branch_id) referencing branches (FK would fail)
-- Precheck: Table visa_import_logs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_import_logs' AND table_schema = DATABASE()
-- Precheck: Table branches exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branches' AND table_schema = DATABASE()
-- Precheck: No orphan rows in visa_import_logs (branch_id) referencing branches (FK would fail). Expect 0: SELECT COUNT(*) FROM `visa_import_logs` c LEFT JOIN `branches` p ON c.`branch_id` = p.`id` WHERE c.`branch_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_import_logs` ADD CONSTRAINT `fk_visa_import_logs_branch_id` FOREIGN KEY (`branch_id`) REFERENCES `branches` (`id`), ALGORITHM=COPY, LOCK=SHARED;
