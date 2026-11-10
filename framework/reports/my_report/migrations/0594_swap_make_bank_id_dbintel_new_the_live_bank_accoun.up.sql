-- Step M594: Swap: make bank_id__dbintel_new the live bank_accounts.bank_id
-- Direction: up
-- Findings: SCH-039-a836d0c5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of bank_id__dbintel_new is complete; bank_id__dbintel_new matches bank_id
-- Precheck: Backfill of bank_id__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `bank_accounts` WHERE `bank_id__dbintel_new` IS NULL AND `bank_id` IS NOT NULL
-- Precheck: bank_id__dbintel_new matches bank_id. Expect 0: SELECT COUNT(*) FROM `bank_accounts` WHERE NOT (`bank_id` <=> `bank_id__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `bank_accounts` RENAME COLUMN `bank_id` TO `bank_id__dbintel_old`;
ALTER TABLE `bank_accounts` RENAME COLUMN `bank_id__dbintel_new` TO `bank_id`;
