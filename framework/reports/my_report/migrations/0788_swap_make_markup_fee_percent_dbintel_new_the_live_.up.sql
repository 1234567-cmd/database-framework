-- Step M788: Swap: make markup_fee_percent__dbintel_new the live maintenance_fee_groups.markup_fee_percent
-- Direction: up
-- Findings: SCH-032-08705923
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of markup_fee_percent__dbintel_new is complete; markup_fee_percent__dbintel_new matches markup_fee_percent
-- Precheck: Backfill of markup_fee_percent__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE `markup_fee_percent__dbintel_new` IS NULL AND `markup_fee_percent` IS NOT NULL
-- Precheck: markup_fee_percent__dbintel_new matches markup_fee_percent. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE NOT (`markup_fee_percent` <=> `markup_fee_percent__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `markup_fee_percent` TO `markup_fee_percent__dbintel_old`;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `markup_fee_percent__dbintel_new` TO `markup_fee_percent`;
