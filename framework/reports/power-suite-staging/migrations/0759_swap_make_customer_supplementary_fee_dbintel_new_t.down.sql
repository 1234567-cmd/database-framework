-- Step M759: Swap: make customer_supplementary_fee__dbintel_new the live invoices.customer_supplementary_fee
-- Direction: down
-- Findings: SCH-023-590a8bc9
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of customer_supplementary_fee__dbintel_new is complete; customer_supplementary_fee__dbintel_new matches customer_supplementary_fee
-- Precheck: Backfill of customer_supplementary_fee__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `invoices` WHERE `customer_supplementary_fee__dbintel_new` IS NULL AND `customer_supplementary_fee` IS NOT NULL
-- Precheck: customer_supplementary_fee__dbintel_new matches customer_supplementary_fee. Expect 0: SELECT COUNT(*) FROM `invoices` WHERE NOT (`customer_supplementary_fee` <=> `customer_supplementary_fee__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoices` RENAME COLUMN `customer_supplementary_fee` TO `customer_supplementary_fee__dbintel_new`;
ALTER TABLE `invoices` RENAME COLUMN `customer_supplementary_fee__dbintel_old` TO `customer_supplementary_fee`;
