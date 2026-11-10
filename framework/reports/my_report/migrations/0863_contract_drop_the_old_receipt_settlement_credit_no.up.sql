-- Step M863: Contract: drop the old receipt_settlement_credit_notes.base_amount__dbintel_old
-- Direction: up
-- Findings: SCH-023-db50882f
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column receipt_settlement_credit_notes.base_amount__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'receipt_settlement_credit_notes' AND table_schema = DATABASE() AND column_name = 'base_amount__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipt_settlement_credit_notes` DROP COLUMN `base_amount__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
