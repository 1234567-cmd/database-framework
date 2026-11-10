-- Step M1008: Add foreign key debit_notes (supplier_id) -> suppliers
-- Direction: up
-- Findings: SCH-002-e9207eed
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in debit_notes (supplier_id) referencing suppliers (FK would fail)
-- Precheck: Table debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'debit_notes' AND table_schema = DATABASE()
-- Precheck: Table suppliers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'suppliers' AND table_schema = DATABASE()
-- Precheck: No orphan rows in debit_notes (supplier_id) referencing suppliers (FK would fail). Expect 0: SELECT COUNT(*) FROM `debit_notes` c LEFT JOIN `suppliers` p ON c.`supplier_id` = p.`id` WHERE c.`supplier_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` ADD CONSTRAINT `fk_debit_notes_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`), ALGORITHM=COPY, LOCK=SHARED;
