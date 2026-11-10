-- Step M903: Expand: add air_travel_cost__dbintel_new decimal(17,4) on service_tours and backfill
-- Direction: down
-- Findings: SCH-023-7c536c6a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table service_tours exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_tours' AND table_schema = DATABASE()
-- Precheck: Column service_tours.air_travel_cost exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_tours' AND table_schema = DATABASE() AND column_name = 'air_travel_cost'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` DROP COLUMN `air_travel_cost__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
