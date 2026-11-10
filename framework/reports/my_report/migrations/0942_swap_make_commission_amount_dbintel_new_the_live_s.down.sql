-- Step M942: Swap: make commission_amount__dbintel_new the live suppliers.commission_amount
-- Direction: down
-- Findings: SCH-023-7ab8005f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of commission_amount__dbintel_new is complete; commission_amount__dbintel_new matches commission_amount
-- Precheck: Backfill of commission_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `suppliers` WHERE `commission_amount__dbintel_new` IS NULL AND `commission_amount` IS NOT NULL
-- Precheck: commission_amount__dbintel_new matches commission_amount. Expect 0: SELECT COUNT(*) FROM `suppliers` WHERE NOT (`commission_amount` <=> `commission_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `suppliers` RENAME COLUMN `commission_amount` TO `commission_amount__dbintel_new`;
ALTER TABLE `suppliers` RENAME COLUMN `commission_amount__dbintel_old` TO `commission_amount`;
