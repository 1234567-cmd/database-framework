-- Step M651: Expand: add group_id__dbintel_new int on cruise_services and backfill
-- Direction: up
-- Findings: SCH-039-b051152f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: cruise_services.group_id holds only integers
-- Precheck: Table cruise_services exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'cruise_services' AND table_schema = DATABASE()
-- Precheck: Column cruise_services.group_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'group_id'
-- Precheck: cruise_services.group_id holds only integers. Expect 0: SELECT COUNT(*) FROM `cruise_services` WHERE `group_id` IS NOT NULL AND (`group_id` NOT REGEXP '^[+-]?[0-9]+$')
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cruise_services` ADD COLUMN `group_id__dbintel_new` int, ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `cruise_services` SET `group_id__dbintel_new` = `group_id` WHERE `group_id__dbintel_new` IS NULL AND `group_id` IS NOT NULL LIMIT 1000;
