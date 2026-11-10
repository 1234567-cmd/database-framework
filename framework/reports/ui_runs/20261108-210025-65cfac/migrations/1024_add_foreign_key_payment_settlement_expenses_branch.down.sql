-- Step M1024: Add foreign key payment_settlement_expenses (branch_id) -> branches
-- Direction: down
-- Findings: SCH-002-f4999ef8
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in payment_settlement_expenses (branch_id) referencing branches (FK would fail)
-- Precheck: Table payment_settlement_expenses exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_expenses' AND table_schema = DATABASE()
-- Precheck: Table branches exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'branches' AND table_schema = DATABASE()
-- Precheck: No orphan rows in payment_settlement_expenses (branch_id) referencing branches (FK would fail). Expect 0: SELECT COUNT(*) FROM `payment_settlement_expenses` c LEFT JOIN `branches` p ON c.`branch_id` = p.`id` WHERE c.`branch_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_expenses` DROP FOREIGN KEY `fk_payment_settlement_expenses_branch_id`;
