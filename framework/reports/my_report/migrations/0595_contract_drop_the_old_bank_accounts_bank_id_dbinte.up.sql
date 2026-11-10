-- Step M595: Contract: drop the old bank_accounts.bank_id__dbintel_old
-- Direction: up
-- Findings: SCH-039-a836d0c5
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column bank_accounts.bank_id__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'bank_accounts' AND table_schema = DATABASE() AND column_name = 'bank_id__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `bank_accounts` DROP COLUMN `bank_id__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
