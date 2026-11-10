-- Step M657: Contract: drop the old customer_contacts.id__dbintel_old
-- Direction: up
-- Findings: SCH-037-41d128ae
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column customer_contacts.id__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_contacts' AND table_schema = DATABASE() AND column_name = 'id__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_contacts` DROP COLUMN `id__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
