-- Step M314: Add column payment_settlement_customer_deposits.currency_code char(3)
-- Direction: up
-- Findings: SCH-024-55389d7b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_customer_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_customer_deposits' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_customer_deposits.currency_code does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_customer_deposits' AND table_schema = DATABASE() AND column_name = 'currency_code'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_customer_deposits` ADD COLUMN `currency_code` char(3), ALGORITHM=INPLACE, LOCK=NONE;
