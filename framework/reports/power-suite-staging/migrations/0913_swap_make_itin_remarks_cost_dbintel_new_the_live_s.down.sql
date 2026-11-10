-- Step M913: Swap: make itin_remarks_cost__dbintel_new the live service_tours.itin_remarks_cost
-- Direction: down
-- Findings: SCH-023-fee5e551
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of itin_remarks_cost__dbintel_new is complete; itin_remarks_cost__dbintel_new matches itin_remarks_cost
-- Precheck: Backfill of itin_remarks_cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE `itin_remarks_cost__dbintel_new` IS NULL AND `itin_remarks_cost` IS NOT NULL
-- Precheck: itin_remarks_cost__dbintel_new matches itin_remarks_cost. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE NOT (`itin_remarks_cost` <=> `itin_remarks_cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` RENAME COLUMN `itin_remarks_cost` TO `itin_remarks_cost__dbintel_new`;
ALTER TABLE `service_tours` RENAME COLUMN `itin_remarks_cost__dbintel_old` TO `itin_remarks_cost`;
