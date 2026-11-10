-- Step M1023: Add foreign key payment_settlement_deposits (supplier_deposit_id) -> supplier_deposits
-- Direction: down
-- Findings: SCH-002-9ff0adbb
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in payment_settlement_deposits (supplier_deposit_id) referencing supplier_deposits (FK would fail)
-- Precheck: Table payment_settlement_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_deposits' AND table_schema = DATABASE()
-- Precheck: Table supplier_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'supplier_deposits' AND table_schema = DATABASE()
-- Precheck: No orphan rows in payment_settlement_deposits (supplier_deposit_id) referencing supplier_deposits (FK would fail). Expect 0: SELECT COUNT(*) FROM `payment_settlement_deposits` c LEFT JOIN `supplier_deposits` p ON c.`supplier_deposit_id` = p.`id` WHERE c.`supplier_deposit_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_deposits` DROP FOREIGN KEY `fk_payment_settlement_deposits_supplier_deposit_id`;
