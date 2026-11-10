-- Step M1044: Add foreign key supplier_deposits (supplier_id) -> suppliers
-- Direction: up
-- Findings: SCH-002-99c38d1f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in supplier_deposits (supplier_id) referencing suppliers (FK would fail)
-- Precheck: Table supplier_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'supplier_deposits' AND table_schema = DATABASE()
-- Precheck: Table suppliers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'suppliers' AND table_schema = DATABASE()
-- Precheck: No orphan rows in supplier_deposits (supplier_id) referencing suppliers (FK would fail). Expect 0: SELECT COUNT(*) FROM `supplier_deposits` c LEFT JOIN `suppliers` p ON c.`supplier_id` = p.`id` WHERE c.`supplier_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `supplier_deposits` ADD CONSTRAINT `fk_supplier_deposits_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`), ALGORITHM=COPY, LOCK=SHARED;
