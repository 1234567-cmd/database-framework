-- Step M907: Swap: make hotel_bookings_cost__dbintel_new the live service_tours.hotel_bookings_cost
-- Direction: up
-- Findings: SCH-023-6f213802
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of hotel_bookings_cost__dbintel_new is complete; hotel_bookings_cost__dbintel_new matches hotel_bookings_cost
-- Precheck: Backfill of hotel_bookings_cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE `hotel_bookings_cost__dbintel_new` IS NULL AND `hotel_bookings_cost` IS NOT NULL
-- Precheck: hotel_bookings_cost__dbintel_new matches hotel_bookings_cost. Expect 0: SELECT COUNT(*) FROM `service_tours` WHERE NOT (`hotel_bookings_cost` <=> `hotel_bookings_cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` RENAME COLUMN `hotel_bookings_cost` TO `hotel_bookings_cost__dbintel_old`;
ALTER TABLE `service_tours` RENAME COLUMN `hotel_bookings_cost__dbintel_new` TO `hotel_bookings_cost`;
