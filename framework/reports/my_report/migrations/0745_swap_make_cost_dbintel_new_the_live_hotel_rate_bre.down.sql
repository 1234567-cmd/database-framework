-- Step M745: Swap: make cost__dbintel_new the live hotel_rate_breakdowns.cost
-- Direction: down
-- Findings: SCH-023-dfec16c6
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of cost__dbintel_new is complete; cost__dbintel_new matches cost
-- Precheck: Backfill of cost__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `hotel_rate_breakdowns` WHERE `cost__dbintel_new` IS NULL AND `cost` IS NOT NULL
-- Precheck: cost__dbintel_new matches cost. Expect 0: SELECT COUNT(*) FROM `hotel_rate_breakdowns` WHERE NOT (`cost` <=> `cost__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_rate_breakdowns` RENAME COLUMN `cost` TO `cost__dbintel_new`;
ALTER TABLE `hotel_rate_breakdowns` RENAME COLUMN `cost__dbintel_old` TO `cost`;
