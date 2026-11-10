-- Step M949: Contract: drop the old tax_rate_maintenance.company_code__dbintel_old
-- Direction: up
-- Findings: SCH-039-adcc1411
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column tax_rate_maintenance.company_code__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tax_rate_maintenance' AND table_schema = DATABASE() AND column_name = 'company_code__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `tax_rate_maintenance` DROP COLUMN `company_code__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
