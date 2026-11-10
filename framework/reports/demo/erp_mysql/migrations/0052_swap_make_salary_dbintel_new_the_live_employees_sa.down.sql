-- Step M052: Swap: make salary__dbintel_new the live employees.salary
-- Direction: down
-- Findings: SCH-020-e58a4292
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of salary__dbintel_new is complete; salary__dbintel_new matches salary
-- Precheck: Backfill of salary__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `employees` WHERE `salary__dbintel_new` IS NULL AND `salary` IS NOT NULL
-- Precheck: salary__dbintel_new matches salary. Expect 0: SELECT COUNT(*) FROM `employees` WHERE NOT (`salary` <=> `salary__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `employees` RENAME COLUMN `salary` TO `salary__dbintel_new`;
ALTER TABLE `employees` RENAME COLUMN `salary__dbintel_old` TO `salary`;
