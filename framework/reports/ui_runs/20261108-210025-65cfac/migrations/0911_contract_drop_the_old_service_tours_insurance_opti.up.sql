-- Step M911: Contract: drop the old service_tours.insurance_options_cost__dbintel_old
-- Direction: up
-- Findings: SCH-023-dd06c261
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column service_tours.insurance_options_cost__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_tours' AND table_schema = DATABASE() AND column_name = 'insurance_options_cost__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_tours` DROP COLUMN `insurance_options_cost__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
