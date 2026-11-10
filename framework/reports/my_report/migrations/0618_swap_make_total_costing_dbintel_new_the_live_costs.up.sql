-- Step M618: Swap: make total_costing__dbintel_new the live costs.total_costing
-- Direction: up
-- Findings: SCH-023-7f4785e7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of total_costing__dbintel_new is complete; total_costing__dbintel_new matches total_costing
-- Precheck: Backfill of total_costing__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `costs` WHERE `total_costing__dbintel_new` IS NULL AND `total_costing` IS NOT NULL
-- Precheck: total_costing__dbintel_new matches total_costing. Expect 0: SELECT COUNT(*) FROM `costs` WHERE NOT (`total_costing` <=> `total_costing__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `costs` RENAME COLUMN `total_costing` TO `total_costing__dbintel_old`;
ALTER TABLE `costs` RENAME COLUMN `total_costing__dbintel_new` TO `total_costing`;
