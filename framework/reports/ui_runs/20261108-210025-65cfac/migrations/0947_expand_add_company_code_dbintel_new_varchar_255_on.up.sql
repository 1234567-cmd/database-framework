-- Step M947: Expand: add company_code__dbintel_new varchar(255) on tax_rate_maintenance and backfill
-- Direction: up
-- Findings: SCH-039-adcc1411
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Could not write a generic check that tax_rate_maintenance.company_code converts from int to varchar(255). Verify conversion by hand before running.; Values in tax_rate_maintenance.company_code fit length 255
-- Precheck: Table tax_rate_maintenance exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tax_rate_maintenance' AND table_schema = DATABASE()
-- Precheck: Column tax_rate_maintenance.company_code exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tax_rate_maintenance' AND table_schema = DATABASE() AND column_name = 'company_code'
-- Precheck: Values in tax_rate_maintenance.company_code fit length 255. Expect 0: SELECT COUNT(*) FROM `tax_rate_maintenance` WHERE `company_code` IS NOT NULL AND (CHAR_LENGTH(`company_code`) > 255)
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `tax_rate_maintenance` ADD COLUMN `company_code__dbintel_new` varchar(255), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `tax_rate_maintenance` SET `company_code__dbintel_new` = `company_code` WHERE `company_code__dbintel_new` IS NULL AND `company_code` IS NOT NULL LIMIT 1000;
