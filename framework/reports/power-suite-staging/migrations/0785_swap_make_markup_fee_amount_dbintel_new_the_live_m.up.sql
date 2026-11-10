-- Step M785: Swap: make markup_fee_amount__dbintel_new the live maintenance_fee_groups.markup_fee_amount
-- Direction: up
-- Findings: SCH-032-d9b0132c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of markup_fee_amount__dbintel_new is complete; markup_fee_amount__dbintel_new matches markup_fee_amount
-- Precheck: Backfill of markup_fee_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE `markup_fee_amount__dbintel_new` IS NULL AND `markup_fee_amount` IS NOT NULL
-- Precheck: markup_fee_amount__dbintel_new matches markup_fee_amount. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE NOT (`markup_fee_amount` <=> `markup_fee_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `markup_fee_amount` TO `markup_fee_amount__dbintel_old`;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `markup_fee_amount__dbintel_new` TO `markup_fee_amount`;
