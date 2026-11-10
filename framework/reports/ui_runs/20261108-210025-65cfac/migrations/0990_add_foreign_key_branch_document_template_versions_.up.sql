-- Step M990: Add foreign key branch_document_template_versions (branch_id) -> branches
-- Direction: up
-- Findings: SCH-002-cfb89799
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in branch_document_template_versions (branch_id) referencing branches (FK would fail)
-- Precheck: Table branch_document_template_versions exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branch_document_template_versions' AND table_schema = DATABASE()
-- Precheck: Table branches exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branches' AND table_schema = DATABASE()
-- Precheck: No orphan rows in branch_document_template_versions (branch_id) referencing branches (FK would fail). Expect 0: SELECT COUNT(*) FROM `branch_document_template_versions` c LEFT JOIN `branches` p ON c.`branch_id` = p.`id` WHERE c.`branch_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `branch_document_template_versions` ADD CONSTRAINT `fk_branch_document_template_versions_branch_id` FOREIGN KEY (`branch_id`) REFERENCES `branches` (`id`), ALGORITHM=COPY, LOCK=SHARED;
