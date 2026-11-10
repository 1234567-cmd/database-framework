-- Step M1021: Add foreign key payment_settlement_customer_transfers (payment_settlement_id) -> payment_settlements
-- Direction: down
-- Findings: SCH-002-8edbd1bb
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in payment_settlement_customer_transfers (payment_settlement_id) referencing payment_settlements (FK would fail)
-- Precheck: Table payment_settlement_customer_transfers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_customer_transfers' AND table_schema = DATABASE()
-- Precheck: Table payment_settlements exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlements' AND table_schema = DATABASE()
-- Precheck: No orphan rows in payment_settlement_customer_transfers (payment_settlement_id) referencing payment_settlements (FK would fail). Expect 0: SELECT COUNT(*) FROM `payment_settlement_customer_transfers` c LEFT JOIN `payment_settlements` p ON c.`payment_settlement_id` = p.`id` WHERE c.`payment_settlement_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_customer_transfers` DROP FOREIGN KEY `fk_payment_settlement_customer_transfers_payment_settlement_id`;
