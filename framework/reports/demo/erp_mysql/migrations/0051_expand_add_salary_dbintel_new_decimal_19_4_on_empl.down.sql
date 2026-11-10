-- Step M051: Expand: add salary__dbintel_new decimal(19,4) on employees and backfill
-- Direction: down
-- Findings: SCH-020-e58a4292
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Could not write a generic check that employees.salary converts from float to decimal(19,4). Verify conversion by hand before running.
-- Precheck: Table employees exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'employees' AND table_schema = DATABASE()
-- Precheck: Column employees.salary exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'employees' AND table_schema = DATABASE() AND column_name = 'salary'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `employees` DROP COLUMN `salary__dbintel_new`, ALGORITHM=INPLACE, LOCK=NONE;
