-- Step M610: Contract: drop the old costs.amount__dbintel_old
-- Direction: up
-- Findings: SCH-023-fe4d9cbe
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column costs.amount__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'costs' AND table_schema = DATABASE() AND column_name = 'amount__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `costs` DROP COLUMN `amount__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
