-- Step M738: Swap: make company_code__dbintel_new the live fee_maintenances.company_code
-- Direction: up
-- Findings: SCH-039-1d3c317f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of company_code__dbintel_new is complete; company_code__dbintel_new matches company_code
-- Precheck: Backfill of company_code__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `fee_maintenances` WHERE `company_code__dbintel_new` IS NULL AND `company_code` IS NOT NULL
-- Precheck: company_code__dbintel_new matches company_code. Expect 0: SELECT COUNT(*) FROM `fee_maintenances` WHERE NOT (`company_code` <=> `company_code__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_maintenances` RENAME COLUMN `company_code` TO `company_code__dbintel_old`;
ALTER TABLE `fee_maintenances` RENAME COLUMN `company_code__dbintel_new` TO `company_code`;
