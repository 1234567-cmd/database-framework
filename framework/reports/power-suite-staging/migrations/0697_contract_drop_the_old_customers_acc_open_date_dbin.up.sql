-- Step M697: Contract: drop the old customers.acc_open_date__dbintel_old
-- Direction: up
-- Findings: SCH-031-9dff568c
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column customers.acc_open_date__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'acc_open_date__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` DROP COLUMN `acc_open_date__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
