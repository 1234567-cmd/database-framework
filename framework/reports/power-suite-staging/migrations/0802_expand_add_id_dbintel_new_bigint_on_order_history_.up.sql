-- Step M802: Expand: add id__dbintel_new bigint on order_history and backfill
-- Direction: up
-- Findings: SCH-037-57ed5a2d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table order_history exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'order_history' AND table_schema = DATABASE()
-- Precheck: Column order_history.id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'order_history' AND table_schema = DATABASE() AND column_name = 'id'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `order_history` ADD COLUMN `id__dbintel_new` bigint, ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `order_history` SET `id__dbintel_new` = `id` WHERE `id__dbintel_new` IS NULL AND `id` IS NOT NULL LIMIT 1000;
