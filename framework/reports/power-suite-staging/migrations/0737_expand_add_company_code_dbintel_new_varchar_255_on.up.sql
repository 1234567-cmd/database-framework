-- Step M737: Expand: add company_code__dbintel_new varchar(255) on fee_maintenances and backfill
-- Direction: up
-- Findings: SCH-039-1d3c317f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Could not write a generic check that fee_maintenances.company_code converts from int to varchar(255). Verify conversion by hand before running.; Values in fee_maintenances.company_code fit length 255
-- Precheck: Table fee_maintenances exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fee_maintenances' AND table_schema = DATABASE()
-- Precheck: Column fee_maintenances.company_code exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_maintenances' AND table_schema = DATABASE() AND column_name = 'company_code'
-- Precheck: Values in fee_maintenances.company_code fit length 255. Expect 0: SELECT COUNT(*) FROM `fee_maintenances` WHERE `company_code` IS NOT NULL AND (CHAR_LENGTH(`company_code`) > 255)
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_maintenances` ADD COLUMN `company_code__dbintel_new` varchar(255), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `fee_maintenances` SET `company_code__dbintel_new` = `company_code` WHERE `company_code__dbintel_new` IS NULL AND `company_code` IS NOT NULL LIMIT 1000;
