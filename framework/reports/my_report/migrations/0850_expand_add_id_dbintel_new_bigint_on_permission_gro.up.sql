-- Step M850: Expand: add id__dbintel_new bigint on permission_groups and backfill
-- Direction: up
-- Findings: SCH-037-d16b2545
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table permission_groups exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'permission_groups' AND table_schema = DATABASE()
-- Precheck: Column permission_groups.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'permission_groups' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `permission_groups` ADD COLUMN `id__dbintel_new` bigint, ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `permission_groups` SET `id__dbintel_new` = `id` WHERE `id__dbintel_new` IS NULL AND `id` IS NOT NULL LIMIT 1000;
