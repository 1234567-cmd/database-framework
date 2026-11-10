-- Step M742: Contract: drop the old hotel_allotment_rooms.cost__dbintel_old
-- Direction: up
-- Findings: SCH-023-34db05ba
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column hotel_allotment_rooms.cost__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotment_rooms' AND table_schema = DATABASE() AND column_name = 'cost__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_allotment_rooms` DROP COLUMN `cost__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
