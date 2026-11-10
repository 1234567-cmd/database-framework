-- Step M1025: Add foreign key payment_settlement_opening_invoices (invoice_id) -> invoices
-- Direction: down
-- Findings: SCH-002-06313896
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: high.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No orphan rows in payment_settlement_opening_invoices (invoice_id) referencing invoices (FK would fail)
-- Precheck: Table payment_settlement_opening_invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_opening_invoices' AND table_schema = DATABASE()
-- Precheck: Table invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoices' AND table_schema = DATABASE()
-- Precheck: No orphan rows in payment_settlement_opening_invoices (invoice_id) referencing invoices (FK would fail). Expect 0: SELECT COUNT(*) FROM `payment_settlement_opening_invoices` c LEFT JOIN `invoices` p ON c.`invoice_id` = p.`id` WHERE c.`invoice_id` IS NOT NULL AND p.`id` IS NULL
-- Note: MySQL only allows INPLACE when foreign_key_checks is off, which would skip validation, so COPY with LOCK=SHARED is used. It blocks writes while running; schedule accordingly.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_opening_invoices` DROP FOREIGN KEY `fk_payment_settlement_opening_invoices_invoice_id`;
