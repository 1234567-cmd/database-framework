-- Step M959: Set customer_deposits.currency_id NOT NULL
-- Direction: down
-- Findings: SCH-006-a9133624
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in customer_deposits.currency_id (NOT NULL would fail)
-- Precheck: Table customer_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_deposits' AND table_schema = DATABASE()
-- Precheck: Column customer_deposits.currency_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_deposits' AND table_schema = DATABASE() AND column_name = 'currency_id'
-- Precheck: No NULLs in customer_deposits.currency_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `customer_deposits` WHERE `currency_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposits` MODIFY COLUMN `currency_id` int NULL, ALGORITHM=INPLACE, LOCK=NONE;
