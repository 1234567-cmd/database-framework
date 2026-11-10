-- Step M701: Expand: add credit_limit__dbintel_new decimal(22,4) on customers and backfill
-- Direction: down
-- Findings: SCH-023-13bd820f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customers' AND table_schema = DATABASE()
-- Precheck: Column customers.credit_limit exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'credit_limit'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` DROP COLUMN `credit_limit__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
