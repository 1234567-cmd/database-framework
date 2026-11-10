-- Step M652: Swap: make group_id__dbintel_new the live cruise_services.group_id
-- Direction: down
-- Findings: SCH-039-b051152f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of group_id__dbintel_new is complete; group_id__dbintel_new matches group_id
-- Precheck: Backfill of group_id__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `cruise_services` WHERE `group_id__dbintel_new` IS NULL AND `group_id` IS NOT NULL
-- Precheck: group_id__dbintel_new matches group_id. Expect 0: SELECT COUNT(*) FROM `cruise_services` WHERE NOT (`group_id` <=> `group_id__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cruise_services` RENAME COLUMN `group_id` TO `group_id__dbintel_new`;
ALTER TABLE `cruise_services` RENAME COLUMN `group_id__dbintel_old` TO `group_id`;
