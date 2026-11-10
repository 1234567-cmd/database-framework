-- Step M979: Set refunds.invoice_id NOT NULL
-- Direction: up
-- Findings: SCH-006-5b495a60
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in refunds.invoice_id (NOT NULL would fail)
-- Precheck: Table refunds exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'refunds' AND table_schema = DATABASE()
-- Precheck: Column refunds.invoice_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'refunds' AND table_schema = DATABASE() AND column_name = 'invoice_id'
-- Precheck: No NULLs in refunds.invoice_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `refunds` WHERE `invoice_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` MODIFY COLUMN `invoice_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
