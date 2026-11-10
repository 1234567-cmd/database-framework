-- Step M053: Contract: drop the old employees.salary__dbintel_old
-- Direction: up
-- Findings: SCH-020-e58a4292
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column employees.salary__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'employees' AND table_schema = DATABASE() AND column_name = 'salary__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `employees` DROP COLUMN `salary__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
