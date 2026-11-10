-- Step M757: Swap: make tax_amount__dbintel_new the live invoice_taxes.tax_amount
-- Direction: down
-- Findings: SCH-023-b8396dd1
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of tax_amount__dbintel_new is complete; tax_amount__dbintel_new matches tax_amount
-- Precheck: Backfill of tax_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `invoice_taxes` WHERE `tax_amount__dbintel_new` IS NULL AND `tax_amount` IS NOT NULL
-- Precheck: tax_amount__dbintel_new matches tax_amount. Expect 0: SELECT COUNT(*) FROM `invoice_taxes` WHERE NOT (`tax_amount` <=> `tax_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoice_taxes` RENAME COLUMN `tax_amount` TO `tax_amount__dbintel_new`;
ALTER TABLE `invoice_taxes` RENAME COLUMN `tax_amount__dbintel_old` TO `tax_amount`;
