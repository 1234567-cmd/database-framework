-- Step M606: Swap: make tax_amount__dbintel_new the live cost_taxes.tax_amount
-- Direction: down
-- Findings: SCH-023-681b12d9
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of tax_amount__dbintel_new is complete; tax_amount__dbintel_new matches tax_amount
-- Precheck: Backfill of tax_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `cost_taxes` WHERE `tax_amount__dbintel_new` IS NULL AND `tax_amount` IS NOT NULL
-- Precheck: tax_amount__dbintel_new matches tax_amount. Expect 0: SELECT COUNT(*) FROM `cost_taxes` WHERE NOT (`tax_amount` <=> `tax_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cost_taxes` RENAME COLUMN `tax_amount` TO `tax_amount__dbintel_new`;
ALTER TABLE `cost_taxes` RENAME COLUMN `tax_amount__dbintel_old` TO `tax_amount`;
