-- Step M599: Swap: make id__dbintel_new the live chart_of_accounts.id
-- Direction: down
-- Findings: SCH-037-8e59c52d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of id__dbintel_new is complete; id__dbintel_new matches id
-- Precheck: Backfill of id__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `chart_of_accounts` WHERE `id__dbintel_new` IS NULL AND `id` IS NOT NULL
-- Precheck: id__dbintel_new matches id. Expect 0: SELECT COUNT(*) FROM `chart_of_accounts` WHERE NOT (`id` <=> `id__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `chart_of_accounts` RENAME COLUMN `id` TO `id__dbintel_new`;
ALTER TABLE `chart_of_accounts` RENAME COLUMN `id__dbintel_old` TO `id`;
