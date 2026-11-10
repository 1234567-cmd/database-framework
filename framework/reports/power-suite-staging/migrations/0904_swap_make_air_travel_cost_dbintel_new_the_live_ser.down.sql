-- Step M904: Swap: make air_travel_cost__dbintel_new the live service_tours.air_travel_cost
-- Direction: down
-- Findings: SCH-023-7c536c6a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of air_travel_cost__dbintel_new is complete; air_travel_cost__dbintel_new matches air_travel_cost
-- Precheck: Backfill of air_travel_cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE `air_travel_cost__dbintel_new` IS NULL AND `air_travel_cost` IS NOT NULL
-- Precheck: air_travel_cost__dbintel_new matches air_travel_cost. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE NOT (`air_travel_cost` <=> `air_travel_cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` RENAME COLUMN `air_travel_cost` TO `air_travel_cost__dbintel_new`;
ALTER TABLE `service_tours` RENAME COLUMN `air_travel_cost__dbintel_old` TO `air_travel_cost`;
