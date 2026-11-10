-- Step M916: Swap: make visa_service_cost__dbintel_new the live service_tours.visa_service_cost
-- Direction: down
-- Findings: SCH-023-dcc141ec
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of visa_service_cost__dbintel_new is complete; visa_service_cost__dbintel_new matches visa_service_cost
-- Precheck: Backfill of visa_service_cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE `visa_service_cost__dbintel_new` IS NULL AND `visa_service_cost` IS NOT NULL
-- Precheck: visa_service_cost__dbintel_new matches visa_service_cost. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE NOT (`visa_service_cost` <=> `visa_service_cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` RENAME COLUMN `visa_service_cost` TO `visa_service_cost__dbintel_new`;
ALTER TABLE `service_tours` RENAME COLUMN `visa_service_cost__dbintel_old` TO `visa_service_cost`;
