-- Step M973: Set receipt_settlement_deposits.customer_deposit_id NOT NULL
-- Direction: up
-- Findings: SCH-006-d822156d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in receipt_settlement_deposits.customer_deposit_id (NOT NULL would fail)
-- Precheck: Table receipt_settlement_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'receipt_settlement_deposits' AND table_schema = DATABASE()
-- Precheck: Column receipt_settlement_deposits.customer_deposit_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'receipt_settlement_deposits' AND table_schema = DATABASE() AND column_name = 'customer_deposit_id'
-- Precheck: No NULLs in receipt_settlement_deposits.customer_deposit_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `receipt_settlement_deposits` WHERE `customer_deposit_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipt_settlement_deposits` MODIFY COLUMN `customer_deposit_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
