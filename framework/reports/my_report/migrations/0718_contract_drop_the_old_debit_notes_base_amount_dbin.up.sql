-- Step M718: Contract: drop the old debit_notes.base_amount__dbintel_old
-- Direction: up
-- Findings: SCH-023-b4105556
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column debit_notes.base_amount__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'debit_notes' AND table_schema = DATABASE() AND column_name = 'base_amount__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` DROP COLUMN `base_amount__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
