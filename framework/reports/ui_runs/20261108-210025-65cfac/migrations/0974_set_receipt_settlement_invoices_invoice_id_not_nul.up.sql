-- Step M974: Set receipt_settlement_invoices.invoice_id NOT NULL
-- Direction: up
-- Findings: SCH-006-6a7c4906
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in receipt_settlement_invoices.invoice_id (NOT NULL would fail)
-- Precheck: Table receipt_settlement_invoices exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'receipt_settlement_invoices' AND table_schema = DATABASE()
-- Precheck: Column receipt_settlement_invoices.invoice_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'receipt_settlement_invoices' AND table_schema = DATABASE() AND column_name = 'invoice_id'
-- Precheck: No NULLs in receipt_settlement_invoices.invoice_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `receipt_settlement_invoices` WHERE `invoice_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipt_settlement_invoices` MODIFY COLUMN `invoice_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
