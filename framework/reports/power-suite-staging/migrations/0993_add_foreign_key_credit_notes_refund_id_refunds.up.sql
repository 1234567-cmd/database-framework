-- Step M993: Add foreign key credit_notes (refund_id) -> refunds
-- Direction: up
-- Findings: SCH-002-b91a9355
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in credit_notes (refund_id) referencing refunds (FK would fail)
-- Precheck: Table credit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'credit_notes' AND table_schema = DATABASE()
-- Precheck: Table refunds exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'refunds' AND table_schema = DATABASE()
-- Precheck: No orphan rows in credit_notes (refund_id) referencing refunds (FK would fail). Expect 0: SELECT COUNT(*) FROM `credit_notes` c LEFT JOIN `refunds` p ON c.`refund_id` = p.`id` WHERE c.`refund_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` ADD CONSTRAINT `fk_credit_notes_refund_id` FOREIGN KEY (`refund_id`) REFERENCES `refunds` (`id`), ALGORITHM=COPY, LOCK=SHARED;
