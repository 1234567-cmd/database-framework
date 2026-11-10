-- Step M747: Expand: add total_amount__dbintel_new decimal(17,4) on import_batches and backfill
-- Direction: up
-- Findings: SCH-023-884420cd
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table import_batches exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'import_batches' AND table_schema = DATABASE()
-- Precheck: Column import_batches.total_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'import_batches' AND table_schema = DATABASE() AND column_name = 'total_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `import_batches` ADD COLUMN `total_amount__dbintel_new` decimal(17,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `import_batches` SET `total_amount__dbintel_new` = `total_amount` WHERE `total_amount__dbintel_new` IS NULL AND `total_amount` IS NOT NULL LIMIT 1000;
