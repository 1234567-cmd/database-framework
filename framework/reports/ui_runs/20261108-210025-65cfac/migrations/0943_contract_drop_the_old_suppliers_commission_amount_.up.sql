-- Step M943: Contract: drop the old suppliers.commission_amount__dbintel_old
-- Direction: up
-- Findings: SCH-023-7ab8005f
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column suppliers.commission_amount__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'suppliers' AND table_schema = DATABASE() AND column_name = 'commission_amount__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `suppliers` DROP COLUMN `commission_amount__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
