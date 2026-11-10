-- Step M111: Add column customer_amends.updated_by varchar(255)
-- Direction: down
-- Findings: SCH-044-6c23e3c2
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_amends exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_amends' AND table_schema = DATABASE()
-- Precheck: Column customer_amends.updated_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_amends' AND table_schema = DATABASE() AND column_name = 'updated_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_amends` DROP COLUMN `updated_by`, ALGORITHM=INPLACE, LOCK=NONE;
