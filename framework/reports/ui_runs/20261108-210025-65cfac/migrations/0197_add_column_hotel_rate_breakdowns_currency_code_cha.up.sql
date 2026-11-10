-- Step M197: Add column hotel_rate_breakdowns.currency_code char(3)
-- Direction: up
-- Findings: SCH-024-b085f9df
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table hotel_rate_breakdowns exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'hotel_rate_breakdowns' AND table_schema = DATABASE()
-- Precheck: Column hotel_rate_breakdowns.currency_code does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_rate_breakdowns' AND table_schema = DATABASE() AND column_name = 'currency_code'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_rate_breakdowns` ADD COLUMN `currency_code` char(3), ALGORITHM=INPLACE, LOCK=NONE;
