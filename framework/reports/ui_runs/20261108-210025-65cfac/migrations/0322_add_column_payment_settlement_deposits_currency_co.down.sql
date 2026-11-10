-- Step M322: Add column payment_settlement_deposits.currency_code char(3)
-- Direction: down
-- Findings: SCH-024-194157f2
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table payment_settlement_deposits exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'payment_settlement_deposits' AND table_schema = DATABASE()
-- Precheck: Column payment_settlement_deposits.currency_code does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'payment_settlement_deposits' AND table_schema = DATABASE() AND column_name = 'currency_code'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_deposits` DROP COLUMN `currency_code`, ALGORITHM=INPLACE, LOCK=NONE;
