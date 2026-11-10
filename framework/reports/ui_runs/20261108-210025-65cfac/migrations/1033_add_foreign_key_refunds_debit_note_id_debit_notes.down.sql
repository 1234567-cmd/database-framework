-- Step M1033: Add foreign key refunds (debit_note_id) -> debit_notes
-- Direction: down
-- Findings: SCH-002-f3bddba9
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in refunds (debit_note_id) referencing debit_notes (FK would fail)
-- Precheck: Table refunds exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'refunds' AND table_schema = DATABASE()
-- Precheck: Table debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'debit_notes' AND table_schema = DATABASE()
-- Precheck: No orphan rows in refunds (debit_note_id) referencing debit_notes (FK would fail). Expect 0: SELECT COUNT(*) FROM `refunds` c LEFT JOIN `debit_notes` p ON c.`debit_note_id` = p.`id` WHERE c.`debit_note_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` DROP FOREIGN KEY `fk_refunds_debit_note_id`;
