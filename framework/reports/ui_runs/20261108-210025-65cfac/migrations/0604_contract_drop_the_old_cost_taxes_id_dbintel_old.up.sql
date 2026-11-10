-- Step M604: Contract: drop the old cost_taxes.id__dbintel_old
-- Direction: up
-- Findings: SCH-037-699d1eb5
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column cost_taxes.id__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cost_taxes' AND table_schema = DATABASE() AND column_name = 'id__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cost_taxes` DROP COLUMN `id__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
