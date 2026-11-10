-- Step M997: Add foreign key customer_deposits (receipt_settlement_id) -> receipt_settlements
-- Direction: down
-- Findings: SCH-002-18ec378a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in customer_deposits (receipt_settlement_id) referencing receipt_settlements (FK would fail)
-- Precheck: Table customer_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_deposits' AND table_schema = DATABASE()
-- Precheck: Table receipt_settlements exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'receipt_settlements' AND table_schema = DATABASE()
-- Precheck: No orphan rows in customer_deposits (receipt_settlement_id) referencing receipt_settlements (FK would fail). Expect 0: SELECT COUNT(*) FROM `customer_deposits` c LEFT JOIN `receipt_settlements` p ON c.`receipt_settlement_id` = p.`id` WHERE c.`receipt_settlement_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposits` DROP FOREIGN KEY `fk_customer_deposits_receipt_settlement_id`;
