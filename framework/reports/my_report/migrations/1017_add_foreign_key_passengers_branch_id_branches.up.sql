-- Step M1017: Add foreign key passengers (branch_id) -> branches
-- Direction: up
-- Findings: SCH-002-46693cd3
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in passengers (branch_id) referencing branches (FK would fail)
-- Precheck: Table passengers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'passengers' AND table_schema = DATABASE()
-- Precheck: Table branches exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branches' AND table_schema = DATABASE()
-- Precheck: No orphan rows in passengers (branch_id) referencing branches (FK would fail). Expect 0: SELECT COUNT(*) FROM `passengers` c LEFT JOIN `branches` p ON c.`branch_id` = p.`id` WHERE c.`branch_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `passengers` ADD CONSTRAINT `fk_passengers_branch_id` FOREIGN KEY (`branch_id`) REFERENCES `branches` (`id`), ALGORITHM=COPY, LOCK=SHARED;
