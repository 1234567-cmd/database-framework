-- Step M953: Swap: make cost_amount__dbintel_new the live visa_code_maintenance.cost_amount
-- Direction: up
-- Findings: SCH-023-c639be29
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of cost_amount__dbintel_new is complete; cost_amount__dbintel_new matches cost_amount
-- Precheck: Backfill of cost_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `visa_code_maintenance` WHERE `cost_amount__dbintel_new` IS NULL AND `cost_amount` IS NOT NULL
-- Precheck: cost_amount__dbintel_new matches cost_amount. Expect 0: SELECT COUNT(*) FROM `visa_code_maintenance` WHERE NOT (`cost_amount` <=> `cost_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_code_maintenance` RENAME COLUMN `cost_amount` TO `cost_amount__dbintel_old`;
ALTER TABLE `visa_code_maintenance` RENAME COLUMN `cost_amount__dbintel_new` TO `cost_amount`;
