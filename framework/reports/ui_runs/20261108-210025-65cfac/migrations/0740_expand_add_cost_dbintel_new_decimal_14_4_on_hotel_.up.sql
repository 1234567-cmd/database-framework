-- Step M740: Expand: add cost__dbintel_new decimal(14,4) on hotel_allotment_rooms and backfill
-- Direction: up
-- Findings: SCH-023-34db05ba
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table hotel_allotment_rooms exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'hotel_allotment_rooms' AND table_schema = DATABASE()
-- Precheck: Column hotel_allotment_rooms.cost exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotment_rooms' AND table_schema = DATABASE() AND column_name = 'cost'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_allotment_rooms` ADD COLUMN `cost__dbintel_new` decimal(14,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `hotel_allotment_rooms` SET `cost__dbintel_new` = `cost` WHERE `cost__dbintel_new` IS NULL AND `cost` IS NOT NULL LIMIT 1000;
