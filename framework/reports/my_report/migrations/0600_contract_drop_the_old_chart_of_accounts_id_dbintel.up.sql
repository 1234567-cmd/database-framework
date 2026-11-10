-- Step M600: Contract: drop the old chart_of_accounts.id__dbintel_old
-- Direction: up
-- Findings: SCH-037-8e59c52d
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column chart_of_accounts.id__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'chart_of_accounts' AND table_schema = DATABASE() AND column_name = 'id__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `chart_of_accounts` DROP COLUMN `id__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
