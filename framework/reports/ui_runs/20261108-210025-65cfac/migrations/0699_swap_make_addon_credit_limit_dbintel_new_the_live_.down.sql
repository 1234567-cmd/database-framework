-- Step M699: Swap: make addon_credit_limit__dbintel_new the live customers.addon_credit_limit
-- Direction: down
-- Findings: SCH-023-b81e798b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of addon_credit_limit__dbintel_new is complete; addon_credit_limit__dbintel_new matches addon_credit_limit
-- Precheck: Backfill of addon_credit_limit__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `customers` WHERE `addon_credit_limit__dbintel_new` IS NULL AND `addon_credit_limit` IS NOT NULL
-- Precheck: addon_credit_limit__dbintel_new matches addon_credit_limit. Expect 0: SELECT COUNT(*) FROM `customers` WHERE NOT (`addon_credit_limit` <=> `addon_credit_limit__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` RENAME COLUMN `addon_credit_limit` TO `addon_credit_limit__dbintel_new`;
ALTER TABLE `customers` RENAME COLUMN `addon_credit_limit__dbintel_old` TO `addon_credit_limit`;
