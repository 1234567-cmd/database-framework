-- Step M741: Swap: make cost__dbintel_new the live hotel_allotment_rooms.cost
-- Direction: up
-- Findings: SCH-023-34db05ba
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of cost__dbintel_new is complete; cost__dbintel_new matches cost
-- Precheck: Backfill of cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `hotel_allotment_rooms` WHERE `cost__dbintel_new` IS NULL AND `cost` IS NOT NULL
-- Precheck: cost__dbintel_new matches cost. Expect 0: SELECT COUNT(*) FROM `hotel_allotment_rooms` WHERE NOT (`cost` <=> `cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_allotment_rooms` RENAME COLUMN `cost` TO `cost__dbintel_old`;
ALTER TABLE `hotel_allotment_rooms` RENAME COLUMN `cost__dbintel_new` TO `cost`;
