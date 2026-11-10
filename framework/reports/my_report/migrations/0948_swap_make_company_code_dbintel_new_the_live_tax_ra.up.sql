-- Step M948: Swap: make company_code__dbintel_new the live tax_rate_maintenance.company_code
-- Direction: up
-- Findings: SCH-039-adcc1411
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of company_code__dbintel_new is complete; company_code__dbintel_new matches company_code
-- Precheck: Backfill of company_code__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `tax_rate_maintenance` WHERE `company_code__dbintel_new` IS NULL AND `company_code` IS NOT NULL
-- Precheck: company_code__dbintel_new matches company_code. Expect 0: SELECT COUNT(*) FROM `tax_rate_maintenance` WHERE NOT (`company_code` <=> `company_code__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `tax_rate_maintenance` RENAME COLUMN `company_code` TO `company_code__dbintel_old`;
ALTER TABLE `tax_rate_maintenance` RENAME COLUMN `company_code__dbintel_new` TO `company_code`;
