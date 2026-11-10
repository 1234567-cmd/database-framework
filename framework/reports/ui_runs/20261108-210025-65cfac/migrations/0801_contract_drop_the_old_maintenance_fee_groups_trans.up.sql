-- Step M801: Contract: drop the old maintenance_fee_groups.transaction_fee_percent__dbintel_old
-- Direction: up
-- Findings: SCH-032-ff76e7a9
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column maintenance_fee_groups.transaction_fee_percent__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE() AND column_name = 'transaction_fee_percent__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` DROP COLUMN `transaction_fee_percent__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
