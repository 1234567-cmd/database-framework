-- Step M910: Swap: make insurance_options_cost__dbintel_new the live service_tours.insurance_options_cost
-- Direction: down
-- Findings: SCH-023-dd06c261
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of insurance_options_cost__dbintel_new is complete; insurance_options_cost__dbintel_new matches insurance_options_cost
-- Precheck: Backfill of insurance_options_cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE `insurance_options_cost__dbintel_new` IS NULL AND `insurance_options_cost` IS NOT NULL
-- Precheck: insurance_options_cost__dbintel_new matches insurance_options_cost. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE NOT (`insurance_options_cost` <=> `insurance_options_cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` RENAME COLUMN `insurance_options_cost` TO `insurance_options_cost__dbintel_new`;
ALTER TABLE `service_tours` RENAME COLUMN `insurance_options_cost__dbintel_old` TO `insurance_options_cost`;
