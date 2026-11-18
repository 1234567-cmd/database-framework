-- Step M739: Contract: drop the old intake_notifications.id__dbintel_old
-- Direction: up
-- Findings: SCH-037-115840ea
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column intake_notifications.id__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'intake_notifications' AND table_schema = DATABASE() AND column_name = 'id__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `intake_notifications` DROP COLUMN `id__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
