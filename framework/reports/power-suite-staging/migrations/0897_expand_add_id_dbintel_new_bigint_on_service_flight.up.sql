-- Step M897: Expand: add id__dbintel_new bigint on service_flights and backfill
-- Direction: up
-- Findings: SCH-037-41f8f984
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table service_flights exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_flights' AND table_schema = DATABASE()
-- Precheck: Column service_flights.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_flights' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_flights` ADD COLUMN `id__dbintel_new` bigint, ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `service_flights` SET `id__dbintel_new` = `id` WHERE `id__dbintel_new` IS NULL AND `id` IS NOT NULL LIMIT 1000;
