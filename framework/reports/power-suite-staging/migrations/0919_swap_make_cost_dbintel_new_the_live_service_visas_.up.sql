-- Step M919: Swap: make cost__dbintel_new the live service_visas.cost
-- Direction: up
-- Findings: SCH-023-a80e7839
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of cost__dbintel_new is complete; cost__dbintel_new matches cost
-- Precheck: Backfill of cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `service_visas` WHERE `cost__dbintel_new` IS NULL AND `cost` IS NOT NULL
-- Precheck: cost__dbintel_new matches cost. Expect 0: SELECT COUNT(*) FROM `service_visas` WHERE NOT (`cost` <=> `cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_visas` RENAME COLUMN `cost` TO `cost__dbintel_old`;
ALTER TABLE `service_visas` RENAME COLUMN `cost__dbintel_new` TO `cost`;
