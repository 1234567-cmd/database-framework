-- Step M612: Swap: make free_of_cost__dbintel_new the live costs.free_of_cost
-- Direction: down
-- Findings: SCH-023-40de7854
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of free_of_cost__dbintel_new is complete; free_of_cost__dbintel_new matches free_of_cost
-- Precheck: Backfill of free_of_cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `costs` WHERE `free_of_cost__dbintel_new` IS NULL AND `free_of_cost` IS NOT NULL
-- Precheck: free_of_cost__dbintel_new matches free_of_cost. Expect 0: SELECT COUNT(*) FROM `costs` WHERE NOT (`free_of_cost` <=> `free_of_cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `costs` RENAME COLUMN `free_of_cost` TO `free_of_cost__dbintel_new`;
ALTER TABLE `costs` RENAME COLUMN `free_of_cost__dbintel_old` TO `free_of_cost`;
